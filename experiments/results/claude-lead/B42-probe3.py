"""B42 probe 3: is the loop residual alloc/free churn? Test free-deferral and chunking."""

from __future__ import annotations

import time

import flopscope as flops
import flopscope.numpy as fnp
from whestbench.dataset import load_dataset, mlp_at

BUDGET = 272_000_000_000
N = 6_500


def ctx_run(fn):
    ctx = flops.BudgetContext(flop_budget=BUDGET, quiet=True)
    with ctx:
        fn()
    return {
        "flops": ctx.flops_used,
        "wall": ctx.wall_time_s,
        "backend": ctx.flopscope_backend_time_s,
        "overhead": ctx.flopscope_overhead_time_s,
        "residual": ctx.residual_wall_time_s,
    }


def report(name, fn, reps=6):
    fn()
    runs = [ctx_run(fn) for _ in range(reps)]
    agg = {k: sum(r[k] for r in runs) / reps for k in runs[0]}
    print(
        f"{name:>38}: flops={agg['flops']:.4g} wall={agg['wall']*1e3:7.2f}ms "
        f"backend={agg['backend']*1e3:7.2f}ms overhead={agg['overhead']*1e3:6.2f}ms "
        f"residual={agg['residual']*1e3:6.2f}ms",
        flush=True,
    )
    return agg


def main():
    ds = load_dataset("aicrowd/arc-whestbench-public-2026", revision="v1-phase1", split="mini")
    mlp = mlp_at(ds, 0)
    weights32 = [w.astype(fnp.float32) for w in mlp.weights]

    rng = fnp.random.default_rng(mlp.seed)
    z = rng.standard_normal((N, 256)).astype(fnp.float32)
    norms = fnp.linalg.norm(z, axis=1)
    u0 = z / norms[:, None]
    hold = {}

    def loop_baseline():
        u = u0
        rows = []
        for w in weights32:
            u = fnp.maximum(fnp.matmul(u, w), 0.0)
            rows.append(fnp.mean(u, axis=0))
        hold["a"] = fnp.stack(rows, axis=0)

    def loop_defer_frees():
        u = u0
        keep = [u0]
        rows = []
        for w in weights32:
            p = fnp.matmul(u, w)
            u = fnp.maximum(p, 0.0)
            keep.append(p)
            keep.append(u)
            rows.append(fnp.mean(u, axis=0))
        hold["keep"] = keep  # frees happen next call / outside ctx
        hold["b"] = fnp.stack(rows, axis=0)

    def make_chunked(chunk):
        def loop_chunked():
            sums = None
            rows_parts = []
            for s in range(0, N, chunk):
                u = u0[s : s + chunk]
                part = []
                for w in weights32:
                    u = fnp.maximum(fnp.matmul(u, w), 0.0)
                    part.append(fnp.sum(u, axis=0))
                rows_parts.append(part)
            layers = []
            for li in range(32):
                acc = rows_parts[0][li]
                for p in rows_parts[1:]:
                    acc = acc + p[li]
                layers.append(acc / float(N))
            hold["c"] = fnp.stack(layers, axis=0)

        return loop_chunked

    report("loop f32 baseline", loop_baseline)
    report("loop f32 defer frees", loop_defer_frees)
    for chunk in (3250, 1625, 812, 406):
        report(f"loop f32 chunked {chunk}", make_chunked(chunk))


if __name__ == "__main__":
    main()
