"""B42 probe 2: micro-attribution of the charged residual by phase.

Isolates (a) the RNG draw, (b) the normalize step, (c) the 32-layer loop,
each under its own BudgetContext, plus draw-dtype and prealloc variants.
"""

from __future__ import annotations

import math
import time

import flopscope as flops
import flopscope.numpy as fnp
from whestbench.dataset import load_dataset, mlp_at

BUDGET = 272_000_000_000
N = 6_500


def ctx_run(fn):
    ctx = flops.BudgetContext(flop_budget=BUDGET, quiet=True)
    t0 = time.perf_counter()
    with ctx:
        fn()
    wall = time.perf_counter() - t0
    return {
        "flops": ctx.flops_used,
        "wall": ctx.wall_time_s,
        "backend": ctx.flopscope_backend_time_s,
        "overhead": ctx.flopscope_overhead_time_s,
        "residual": ctx.residual_wall_time_s,
        "outer_wall": wall,
    }


def report(name, fn, reps=6):
    fn()  # warm
    runs = [ctx_run(fn) for _ in range(reps)]
    agg = {k: sum(r[k] for r in runs) / reps for k in runs[0]}
    print(
        f"{name:>34}: flops={agg['flops']:.4g} wall={agg['wall']*1e3:7.2f}ms "
        f"backend={agg['backend']*1e3:7.2f}ms overhead={agg['overhead']*1e3:6.2f}ms "
        f"residual={agg['residual']*1e3:6.2f}ms charged={1e11*agg['residual']:.3g}",
        flush=True,
    )
    return agg


def main():
    ds = load_dataset("aicrowd/arc-whestbench-public-2026", revision="v1-phase1", split="mini")
    mlp = mlp_at(ds, 0)
    weights64 = list(mlp.weights)
    weights32 = [w.astype(fnp.float32) for w in weights64]

    rng_holder = {}

    def draw64():
        rng = fnp.random.default_rng(mlp.seed)
        rng_holder["z64"] = rng.standard_normal((N, 256))

    def draw32():
        rng = fnp.random.default_rng(mlp.seed)
        rng_holder["z32"] = rng.standard_normal((N, 256), dtype=fnp.float32)

    def draw64_cast():
        rng = fnp.random.default_rng(mlp.seed)
        rng_holder["z64c"] = rng.standard_normal((N, 256)).astype(fnp.float32)

    report("rng draw f64", draw64)
    report("rng draw f32 direct", draw32)
    report("rng draw f64 + astype f32", draw64_cast)

    z32 = rng_holder["z32"]

    def normalize():
        norms = fnp.linalg.norm(z32, axis=1)
        rng_holder["u"] = z32 / norms[:, None]

    report("normalize (norm + divide)", normalize)
    u0 = rng_holder["u"]

    def loop64():
        u = u0.astype(fnp.float64)
        rows = []
        for w in weights64:
            u = fnp.maximum(fnp.matmul(u, w), 0.0)
            rows.append(fnp.mean(u, axis=0))
        rng_holder["out64"] = fnp.stack(rows, axis=0)

    def loop32_cast_inside():
        u = u0
        rows = []
        for w in weights64:
            u = fnp.maximum(fnp.matmul(u, w.astype(fnp.float32)), 0.0)
            rows.append(fnp.mean(u, axis=0))
        rng_holder["out32a"] = fnp.stack(rows, axis=0)

    def loop32_precast():
        u = u0
        rows = []
        for w in weights32:
            u = fnp.maximum(fnp.matmul(u, w), 0.0)
            rows.append(fnp.mean(u, axis=0))
        rng_holder["out32b"] = fnp.stack(rows, axis=0)

    def loop32_nomean():
        u = u0
        for w in weights32:
            u = fnp.maximum(fnp.matmul(u, w), 0.0)
        rng_holder["out32c"] = u

    def loop32_matmul_only():
        u = u0
        for w in weights32:
            u = fnp.matmul(u, w)
        rng_holder["out32d"] = u

    report("loop f64 (champion-like)", loop64)
    report("loop f32 (cast w inside)", loop32_cast_inside)
    report("loop f32 (w precast, no charge)", loop32_precast)
    report("loop f32 no mean", loop32_nomean)
    report("loop f32 matmul only (no relu)", loop32_matmul_only)

    e_r = math.sqrt(2.0) * math.exp(math.lgamma(257 / 2.0) - math.lgamma(256 / 2.0))

    def full_f32_direct_draw():
        rng = fnp.random.default_rng(mlp.seed)
        z = rng.standard_normal((N, 256), dtype=fnp.float32)
        norms = fnp.linalg.norm(z, axis=1)
        u = z / norms[:, None]
        rows = []
        for w in weights64:
            u = fnp.maximum(fnp.matmul(u, w.astype(fnp.float32)), 0.0)
            rows.append(fnp.mean(u, axis=0))
        rng_holder["final"] = e_r * fnp.stack(rows, axis=0)

    report("FULL f32 + direct f32 draw", full_f32_direct_draw, reps=8)


if __name__ == "__main__":
    main()
