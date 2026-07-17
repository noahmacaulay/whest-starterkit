"""B42 probe: attribute the champion's charged residual wall time.

Read-only measurement (no harness modification). Loads 3 real Mini MLPs,
runs the champion predict() and instrumentation-variants under fresh
BudgetContexts, and prints the exact timing decomposition the scorer uses:
    residual = wall - flopscope_backend_time - flopscope_overhead_time
    effective_compute = flops_used + 1e11 * residual

Run: uv run --frozen python experiments/results/claude-lead/B42-probe.py
"""

from __future__ import annotations

import importlib.util
import json
import math
import time

import flopscope as flops
import flopscope.numpy as fnp
from whestbench.dataset import load_dataset, mlp_at

DATASET = "aicrowd/arc-whestbench-public-2026"
REVISION = "v1-phase1"
BUDGET = 272_000_000_000


def load_champion():
    spec = importlib.util.spec_from_file_location("champ", "estimator.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Estimator()


def run_under_budget(fn, mlp):
    ctx = flops.BudgetContext(flop_budget=BUDGET, quiet=True)
    with ctx:
        fn(mlp, BUDGET)
    return {
        "flops_used": ctx.flops_used,
        "wall_s": ctx.wall_time_s,
        "backend_s": ctx.flopscope_backend_time_s,
        "overhead_s": ctx.flopscope_overhead_time_s,
        "residual_s": ctx.residual_wall_time_s,
        "effective": ctx.flops_used + 1e11 * (ctx.residual_wall_time_s or 0.0),
    }


# ---- predict variants (all statistically identical or negligibly different) --

N_SAMPLES = 6_500


def predict_champion_f64_chain(mlp, budget):
    """Exact copy of the champion's predict body."""
    width = mlp.width
    rng = fnp.random.default_rng(mlp.seed)
    z = rng.standard_normal((N_SAMPLES, width)).astype(fnp.float32)
    norms = fnp.linalg.norm(z, axis=1)
    u = z / norms[:, None]
    rows = []
    for w in mlp.weights:
        u = fnp.maximum(fnp.matmul(u, w), 0.0)
        rows.append(fnp.mean(u, axis=0))
    e_r = math.sqrt(2.0) * math.exp(
        math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
    )
    return e_r * fnp.stack(rows, axis=0)


def predict_no_astype(mlp, budget):
    """Champion minus the astype(float32) copy (pure float64 end to end)."""
    width = mlp.width
    rng = fnp.random.default_rng(mlp.seed)
    z = rng.standard_normal((N_SAMPLES, width))
    norms = fnp.linalg.norm(z, axis=1)
    u = z / norms[:, None]
    rows = []
    for w in mlp.weights:
        u = fnp.maximum(fnp.matmul(u, w), 0.0)
        rows.append(fnp.mean(u, axis=0))
    e_r = math.sqrt(2.0) * math.exp(
        math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
    )
    return e_r * fnp.stack(rows, axis=0)


def predict_full_f32(mlp, budget):
    """Whole chain in float32: weights cast once, activations stay float32."""
    width = mlp.width
    rng = fnp.random.default_rng(mlp.seed)
    z = rng.standard_normal((N_SAMPLES, width)).astype(fnp.float32)
    norms = fnp.linalg.norm(z, axis=1)
    u = z / norms[:, None]
    rows = []
    for w in mlp.weights:
        u = fnp.maximum(fnp.matmul(u, w.astype(fnp.float32)), 0.0)
        rows.append(fnp.mean(u, axis=0))
    e_r = math.sqrt(2.0) * math.exp(
        math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
    )
    return e_r * fnp.stack(rows, axis=0)


def make_sectioned(section_times):
    """Champion body with per-section perf_counter gaps recorded."""

    def predict_sectioned(mlp, budget):
        width = mlp.width
        t0 = time.perf_counter()
        rng = fnp.random.default_rng(mlp.seed)
        z = rng.standard_normal((N_SAMPLES, width))
        t1 = time.perf_counter()
        z = z.astype(fnp.float32)
        t2 = time.perf_counter()
        norms = fnp.linalg.norm(z, axis=1)
        u = z / norms[:, None]
        t3 = time.perf_counter()
        rows = []
        for w in mlp.weights:
            u = fnp.maximum(fnp.matmul(u, w), 0.0)
            rows.append(fnp.mean(u, axis=0))
        t4 = time.perf_counter()
        e_r = math.sqrt(2.0) * math.exp(
            math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
        )
        out = e_r * fnp.stack(rows, axis=0)
        t5 = time.perf_counter()
        section_times.append(
            {
                "rng_draw": t1 - t0,
                "astype": t2 - t1,
                "normalize": t3 - t2,
                "layer_loop": t4 - t3,
                "finalize": t5 - t4,
            }
        )
        return out

    return predict_sectioned


def main():
    ds = load_dataset(DATASET, revision=REVISION, split="mini")
    mlps = [mlp_at(ds, i) for i in range(3)]
    print("weights dtype:", mlps[0].weights[0].dtype, flush=True)

    champion = load_champion()

    variants = {
        "champion_estimator_py": lambda m, b: champion.predict(m, b),
        "inline_copy_of_champion": predict_champion_f64_chain,
        "no_astype_f64": predict_no_astype,
        "full_f32_chain": predict_full_f32,
    }

    # Warm-up (imports, BLAS thread pools, dataset page cache) - not measured.
    for fn in variants.values():
        fn(mlps[0], BUDGET)

    results = {}
    for name, fn in variants.items():
        runs = [run_under_budget(fn, m) for m in mlps for _ in range(2)]
        agg = {
            k: sum(r[k] for r in runs) / len(runs)
            for k in ["flops_used", "wall_s", "backend_s", "overhead_s", "residual_s", "effective"]
        }
        results[name] = agg
        print(f"\n== {name} ==")
        for k, v in agg.items():
            print(f"  {k:>12}: {v:.6g}")
        print(f"  multiplier : {max(0.1, agg['effective'] / BUDGET):.6f}")

    # Section-gap attribution for the champion body.
    section_times = []
    sect_fn = make_sectioned(section_times)
    sect_fn(mlps[0], BUDGET)  # warm
    section_times.clear()
    sect_stats = [run_under_budget(sect_fn, m) for m in mlps for _ in range(2)]
    mean_sections = {
        k: sum(s[k] for s in section_times) / len(section_times) for k in section_times[0]
    }
    mean_resid = sum(s["residual_s"] for s in sect_stats) / len(sect_stats)
    print("\n== champion section wall times (s, incl. backend+overhead) ==")
    for k, v in mean_sections.items():
        print(f"  {k:>12}: {v:.6f}")
    print(f"  measured charged residual for sectioned run: {mean_resid:.6f}")

    # MSE sanity: full_f32 vs champion predictions on the 3 MLPs.
    import numpy as np

    for m in mlps:
        a = np.asarray(champion.predict(m, BUDGET))
        b = np.asarray(predict_full_f32(m, BUDGET))
        diff = float(np.max(np.abs(a - b)))
        rel = float(np.max(np.abs(a - b) / (np.abs(a) + 1e-12)))
        print(f"f32-vs-champion prediction diff {m.name}: max_abs={diff:.3e} max_rel={rel:.3e}")

    with open(
        "experiments/results/claude-lead/B42-probe-output.json", "w", encoding="utf-8"
    ) as fh:
        json.dump({"variants": results, "sections": mean_sections}, fh, indent=1)


if __name__ == "__main__":
    main()
