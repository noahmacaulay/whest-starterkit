"""B45 candidate (claude-lead): B43's exact-Haar orthogonal directions
rebuilt on B42's residual-minimized forward structure.

Directions are generated exactly as B43's candidate (candidate_claude.py @
56c3f41) does -- same seeded draw order, same float32 QR blocks, same
sign correction, same 100 iid tail rows -- so the per-MLP statistics that
B44 verified on the complete Full split carry over up to float32 forward
rounding. The forward pass then uses B42's structure: float32 weights,
650-row chunks (allocator arena reuse eliminates the OS memory churn that
flopscope charges as residual wall time at 1e11 FLOPs/s), per-layer sums
accumulated in float64, scaled once by the closed-form chi(width) mean
radius.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path

import flopscope.numpy as fnp
from whestbench import MLP, BaseEstimator


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """Radial-exact MC over exact-Haar orthogonal direction blocks.

        Sampling law (B43/B22): 25 blocks of exact-Haar orthonormal
        directions via `fnp.linalg.qr` of a seeded Gaussian (width,width)
        matrix, sign-corrected by sign(diag(R)) so each Q is exactly
        Haar-distributed; rows are mutually-orthogonal unit directions
        with exactly uniform sphere marginals, so the sample mean stays
        unbiased while within-block negative dependence cuts variance.
        25*256 = 6400 rows plus 100 iid normalized rows = 6500 directions.
        The QR runs through instrumented fnp, so it charges only its
        symbolic FLOPs (~1.15e9 total, +4.2% raw) and its backend wall
        time is free (B22's +149% penalty was plain-numpy invisibility).

        Radial exactness (B25): bias-free ReLU nets are exactly
        positively homogeneous, so E[f(z)] = E[r]*E[f(u)] with the
        closed-form chi(d) mean E[r]; only directions are forwarded.

        Forward structure (B42): float32 weights, 650-row chunks so every
        temporary is ~650KB and the allocator recycles arenas instead of
        OS-level alloc/free churn (the only wall time the scorer charges,
        at 1e11 FLOPs/s); per-layer sums accumulate in float64, matching
        the float64 forward within ~1e-7 absolute.
        """
        _ = budget
        width = mlp.width
        n_blocks = 25          # 25*256 = 6400 orthogonal rows
        n_extra = 100          # + 100 iid rows = 6500 total
        n_samples = n_blocks * width + n_extra
        chunk = 650

        rng = fnp.random.default_rng(mlp.seed)

        blocks = []
        for _b in range(n_blocks):
            g = rng.standard_normal((width, width)).astype(fnp.float32)
            q, r = fnp.linalg.qr(g)
            # Sign-correct columns by sign(diag(R)) -> Q is exactly Haar.
            q = q * fnp.sign(fnp.diagonal(r))
            blocks.append(q)

        z = rng.standard_normal((n_extra, width)).astype(fnp.float32)
        z = z / fnp.linalg.norm(z, axis=1)[:, None]
        blocks.append(z)

        u_all = fnp.concatenate(blocks, axis=0)  # (6500, width) unit rows

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
