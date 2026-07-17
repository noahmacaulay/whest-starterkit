"""Your estimator. Edit `predict()`. Run `python estimator.py` to iterate.

Stage 1 of the WhestBench ladder: just `flopscope` and the local engine. No CLI
knowledge required. Once `predict()` returns something interesting, climb to
Stage 2: `whest validate --estimator estimator.py`.
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
        """B43: radial-exact MC with exact-Haar ORTHOGONAL directions (B22
        done right -- all through instrumented flopscope ops).

        B25's radial-exact substitution (below) forwards uniform-sphere
        directions and scales the layer means by the closed-form chi-mean
        E[r]. B22 showed that replacing i.i.d. sphere directions with
        blocks of mutually-orthogonal (Haar) directions lowers the
        final-layer MC variance by ~5.5% (the anti-correlated orthogonal
        samples cover the sphere more evenly). B22's compute penalty
        (+149% effective compute) was an INSTRUMENTATION ARTIFACT: its
        candidate generated the QR with PLAIN numpy, invisible to
        flopscope, so the ~0.5s/MLP of QR wall time was charged as
        residual at lambda=1e11 FLOPs/s. The scoring model
        (C = flops_used + 1e11*residual_wall_time_s;
        residual = wall - backend - overhead) never charges the wall
        time of INSTRUMENTED fnp ops -- only their symbolic FLOPs. So
        doing the QR through `fnp.linalg.qr` charges only ~4.59e7 FLOPs
        per 256x256 block (~1.15e9 for 25 blocks, +4.2% on raw FLOPs) with
        its backend wall time free.

        Construction: 25 blocks of exact-Haar orthonormal directions via
        `fnp.linalg.qr` of a Gaussian matrix, sign-corrected by
        sign(diag(R)) so the orthogonal matrix is Haar-distributed (its
        rows are then uniform-marginal, mutually-orthogonal unit
        directions -- no radii needed, radial-exact handles magnitude).
        25*256 = 6400 orthogonal rows plus 100 i.i.d. normalized rows =
        6500 directions, matching the champion's sample budget. Forward
        all rows through the 32 layers, take per-layer means, scale by
        E[r] = sqrt(2)*exp(lgamma((d+1)/2) - lgamma(d/2)).

        Unbiased: each row is marginally uniform on the sphere (Haar rows
        and normalized-Gaussian rows alike), so the sample mean is an
        unbiased estimator of E[f(u)]; orthogonality only reduces its
        variance. Radial-exactness is preserved exactly (rows are unit
        vectors; magnitude comes entirely from the E[r] scale).
        """
        _ = budget
        width = mlp.width
        n_blocks = 25          # 25*256 = 6400 orthogonal rows
        n_extra = 100          # + 100 iid rows = 6500 total (champion budget)

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

        u = fnp.concatenate(blocks, axis=0)  # (6500, width) unit directions

        rows = []
        for w in mlp.weights:
            u = fnp.maximum(fnp.matmul(u, w), 0.0)
            rows.append(fnp.mean(u, axis=0))

        e_r = math.sqrt(2.0) * math.exp(
            math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
        )
        return e_r * fnp.stack(rows, axis=0)


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
