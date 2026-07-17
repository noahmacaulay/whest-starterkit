"""B42 candidate (claude-lead): champion with the charged residual minimized.

Identical estimator to the B25 radial-exact champion (same seeded draw, same
directions, same statistics); only the arithmetic is restructured so that the
un-instrumented wall time flopscope charges as residual (at 1e11 FLOPs/s)
nearly vanishes: float32 forward chain (halves memory traffic) computed in
650-row chunks (keeps every temporary small enough for allocator arena reuse
instead of OS-level churn), with per-layer sums accumulated in float64 so the
final layer means match the champion's to ~7e-8 absolute.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path

import flopscope as flops
import flopscope.numpy as fnp
from whestbench import MLP, BaseEstimator

_COV_RESCALE_THRESHOLD = 1e100


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """Radial-exact Monte Carlo (B25) with minimized charged residual (B42).

        For z ~ N(0, I_d), z = r*u with r = ||z|| ~ chi(d), u = z/r ~
        Uniform(sphere), r independent of u. `MLP` has no bias field, so
        the ReLU forward pass is exactly positively homogeneous:
        f(c*x) = c*f(x) for c > 0. Hence E[f(z)] = E[r]*E[f(u)] exactly --
        substitute the closed-form E[r] for the sampled radius and
        forward only directions.

        B42 restructuring (statistically identical, near-bit-identical
        predictions): the scorer charges effective compute
        C = flops_used + 1e11 * (wall - backend - overhead), so only
        un-instrumented time (allocator/OS churn between fnp ops) costs
        score. Forwarding the same 6,500 directions in float32 and in
        650-row chunks keeps every temporary ~650KB, which the process
        allocator recycles without OS-level alloc/free churn; per-layer
        sums accumulate in float64 so the returned means match the
        float64 champion to ~1e-7 absolute (MSE change < 1e-15).
        """
        n_samples = 6_500
        chunk = 650
        _ = budget
        width = mlp.width

        rng = fnp.random.default_rng(mlp.seed)
        z = rng.standard_normal((n_samples, width)).astype(fnp.float32)
        norms = fnp.linalg.norm(z, axis=1)
        u_all = z / norms[:, None]

        w32 = [w.astype(fnp.float32) for w in mlp.weights]

        acc = None
        for start in range(0, n_samples, chunk):
            u = u_all[start : start + chunk]
            sums = []
            for w in w32:
                u = fnp.maximum(fnp.matmul(u, w), 0.0)
                sums.append(fnp.sum(u, axis=0, dtype=fnp.float64))
            acc = sums if acc is None else [a + b for a, b in zip(acc, sums)]

        e_r = math.sqrt(2.0) * math.exp(
            math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
        )
        return (e_r / n_samples) * fnp.stack(acc, axis=0)


def _load_baseline(name: str) -> type[BaseEstimator]:
    """Load the `Estimator` class from `examples/<name>.py` or `examples/0N_<name>.py`."""
    examples_dir = Path(__file__).resolve().parent / "examples"
    candidates = [examples_dir / f"{name}.py", *examples_dir.glob(f"??_{name}.py")]
    for candidate in candidates:
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location(candidate.stem, candidate)
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.Estimator
    raise SystemExit(
        f"\n[whest-starterkit] Could not find baseline `{name}` in examples/.\n"
        f"Available: {sorted(p.name for p in examples_dir.glob('*.py'))}\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Iterate on your estimator locally.")
    parser.add_argument(
        "--baseline",
        default=None,
        help="Compare your estimator against an example: 'random', 'mean_propagation', "
        "or 'covariance_propagation'.",
    )
    parser.add_argument("--width", type=int, default=256)
    parser.add_argument("--depth", type=int, default=32)  # phase-1 competition shape (warmup was 8)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    from local_engine import build_mlp, compare_against_monte_carlo

    mlp = build_mlp(width=args.width, depth=args.depth, seed=args.seed)

    print("--- Your estimator ---")
    compare_against_monte_carlo(Estimator(), mlp)

    if args.baseline:
        baseline_cls = _load_baseline(args.baseline)
        print(f"\n--- Baseline: {args.baseline} ---")
        compare_against_monte_carlo(baseline_cls(), mlp)
