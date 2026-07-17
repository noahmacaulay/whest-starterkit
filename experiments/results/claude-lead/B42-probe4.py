"""B42 probe 4: full candidate end-to-end vs champion; chunk-size selection + MSE sanity."""

from __future__ import annotations

import importlib.util
import math

import numpy as np

import flopscope as flops
import flopscope.numpy as fnp
from whestbench.dataset import load_dataset, mlp_at

BUDGET = 272_000_000_000
N = 6_500


def load_champion():
    spec = importlib.util.spec_from_file_location("champ", "estimator.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Estimator()


def make_candidate(chunk):
    def predict(mlp, budget):
        width = mlp.width
        rng = fnp.random.default_rng(mlp.seed)
        z = rng.standard_normal((N, width)).astype(fnp.float32)
        norms = fnp.linalg.norm(z, axis=1)
        u_all = z / norms[:, None]
        w32 = [w.astype(fnp.float32) for w in mlp.weights]
        acc = None
        for s in range(0, N, chunk):
            u = u_all[s : s + chunk]
            sums = []
            for w in w32:
                u = fnp.maximum(fnp.matmul(u, w), 0.0)
                sums.append(fnp.sum(u, axis=0, dtype=fnp.float64))
            acc = sums if acc is None else [a + b for a, b in zip(acc, sums)]
        e_r = math.sqrt(2.0) * math.exp(
            math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
        )
        return (e_r / N) * fnp.stack(acc, axis=0)

    return predict


def ctx_run(fn, mlp):
    ctx = flops.BudgetContext(flop_budget=BUDGET, quiet=True)
    with ctx:
        out = fn(mlp, BUDGET)
    return ctx, out


def bench(name, fn, mlps, reps=3):
    fn(mlps[0], BUDGET)
    stats = []
    for m in mlps:
        for _ in range(reps):
            ctx, _ = ctx_run(fn, m)
            stats.append(
                (ctx.flops_used, ctx.wall_time_s, ctx.flopscope_backend_time_s,
                 ctx.flopscope_overhead_time_s, ctx.residual_wall_time_s)
            )
    n = len(stats)
    fl, wa, ba, ov, re = (sum(s[i] for s in stats) / n for i in range(5))
    eff = fl + 1e11 * re
    print(
        f"{name:>22}: flops={fl:.6g} wall={wa*1e3:6.1f}ms backend={ba*1e3:6.1f}ms "
        f"overhead={ov*1e3:6.1f}ms residual={re*1e3:6.2f}ms effective={eff:.6g} "
        f"mult={max(0.1, eff/BUDGET):.6f}",
        flush=True,
    )
    return eff


def main():
    ds = load_dataset("aicrowd/arc-whestbench-public-2026", revision="v1-phase1", split="mini")
    mlps = [mlp_at(ds, i) for i in range(3)]
    champion = load_champion()

    eff_champ = bench("champion", lambda m, b: champion.predict(m, b), mlps)
    for chunk in (1300, 650, 500, 325):
        eff = bench(f"candidate chunk={chunk}", make_candidate(chunk), mlps)
        print(f"{'':>22}  -> vs champion: {100.0 * (eff / eff_champ - 1):+.2f}% effective compute")

    # Prediction/MSE sanity on the 3 MLPs (vs champion + vs dataset truth).
    cand = make_candidate(650)
    for i, m in enumerate(mlps):
        a = np.asarray(champion.predict(m, BUDGET))
        b = np.asarray(cand(m, BUDGET))
        row = ds[i]
        truth = np.asarray(row["final_means"], dtype=np.float64)
        mse_a = float(np.mean((a[-1] - truth) ** 2))
        mse_b = float(np.mean((b[-1] - truth) ** 2))
        print(
            f"{m.name}: final-layer MSE champion={mse_a:.6e} candidate={mse_b:.6e} "
            f"rel_change={100.0 * (mse_b / mse_a - 1):+.3f}%  max|a-b|={np.max(np.abs(a - b)):.2e}"
        )


if __name__ == "__main__":
    main()
