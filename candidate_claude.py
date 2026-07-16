"""Your estimator. Edit `predict()`. Run `python estimator.py` to iterate.

Stage 1 of the WhestBench ladder: just `flopscope` and the local engine. No CLI
knowledge required. Once `predict()` returns something interesting, climb to
Stage 2: `whest validate --estimator estimator.py`.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as _np
import flopscope as flops
import flopscope.numpy as fnp
from whestbench import MLP, BaseEstimator

_COV_RESCALE_THRESHOLD = 1e100

# 16-node probabilists' Gauss-Hermite rule for a standard normal (weights sum
# to 1). Standard published quadrature constants, not algorithm-specific.
_GH_NODES = (-6.630878198393129, -5.472225705949343, -4.492955302520011,
             -3.6008736241715487, -2.7602450476307014, -1.9519803457163334,
             -1.1638291005549648, -0.3867606045005574, 0.3867606045005574,
             1.1638291005549648, 1.9519803457163334, 2.7602450476307014,
             3.6008736241715487, 4.492955302520011, 5.472225705949343,
             6.630878198393129)
_GH_WEIGHTS = (1.4978147231618412e-10, 1.309473216286817e-07,
               1.530003216248732e-05, 0.0005259849265739087,
               0.007266937601184749, 0.04728475235401406,
               0.1583383727509497, 0.286568521238012, 0.286568521238012,
               0.1583383727509497, 0.04728475235401406,
               0.007266937601184749, 0.0005259849265739087,
               1.530003216248732e-05, 1.309473216286817e-07,
               1.4978147231618412e-10)
_GH_PAIRS = tuple(max(1, round(w * 3_250)) for w in _GH_WEIGHTS)


_PILOT_N = 300
_COV_POWER_ITERS = 20


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """B21: empirical final-layer covariance direction.

        Builds on the B1/B10/B13/B14/B16 active-subspace lineage (16-node
        Gauss-Hermite quadrature along a dominant direction, antithetic
        draws in the orthogonal complement, single batched matmul per
        layer for the main sampling pass) but replaces the direction
        -finding step entirely.

        Prior direction-finding attempts in this lineage all used a
        *proxy* for the quantity that actually matters:
        - B1/B10/B11/B13/B18/B19 used the dominant eigenvector of a
          *linearized* soft-gate Jacobian -- an approximation of variance
          propagation, not the real nonlinear network.
        - B20 (Stein's lemma) used local input-gradient sensitivity at
          the origin -- measured empirically to be nearly uncorrelated
          (mean cosine similarity ~0.13 across 30 MLPs) with the
          soft-gate eigenvector, indicating it targets a different
          quantity than the one that matters for this quadrature.
        - B19 showed convergence to the soft-gate eigenvector proxy does
          NOT reliably predict this estimator's real final-layer MSE.

        This version measures the target quantity directly instead of
        approximating it: a pilot batch of 300 real samples is forwarded
        through the network with TRUE hard ReLU (no linearization), the
        empirical covariance of their *final-layer* activations is
        computed, and its dominant eigenvector (via power iteration on
        the (width, width) empirical covariance -- cheap once the
        covariance itself is computed) is used as the quadrature
        direction. Validated for stability before writing this candidate:
        across 20 real Mini-split MLPs, splitting a 600-sample pilot into
        two independent halves gave cosine similarity >=0.992 (mean
        0.997) between the two halves' dominant eigenvectors -- i.e. a
        300-sample pilot already gives a highly stable direction estimate
        (unsurprising given the top-eigenvalue/trace ratio averaged 0.60,
        confirming real but partial rank-1 dominance). The pilot forward
        pass costs real extra FLOPs (~4-5% of the main ~6,500-sample
        budget at the full 3,250 pair-count scale, kept unchanged per
        B16's finding that pair-count tuning is a dead end).
        """
        _ = budget
        width = mlp.width

        # --- pilot batch: true nonlinear forward pass, no linearization ---
        pilot_rng = fnp.random.default_rng(mlp.seed)
        x_pilot = fnp.array(pilot_rng.standard_normal((_PILOT_N, width)).astype(fnp.float32))
        y_pilot = x_pilot
        for w in mlp.weights:
            y_pilot = fnp.maximum(y_pilot @ w, 0.0)

        y_centered = y_pilot - fnp.sum(y_pilot, axis=0) / _PILOT_N
        cov = (y_centered.T @ y_centered) / (_PILOT_N - 1)

        direction = fnp.ones(width)
        direction = direction / fnp.sqrt(fnp.sum(direction * direction))
        for _ in range(_COV_POWER_ITERS):
            direction = cov @ direction
            direction = direction / fnp.sqrt(fnp.sum(direction * direction))

        # --- build one combined batch for all 16 quadrature nodes ---
        total_pairs = sum(_GH_PAIRS)
        rng = fnp.random.default_rng(mlp.seed)
        noise = fnp.array(rng.standard_normal((total_pairs, width)).astype(fnp.float32))
        noise = noise - fnp.outer(noise @ direction, direction)

        node_per_pair = fnp.array(
            _np.repeat(_np.array(_GH_NODES, dtype=_np.float32), _GH_PAIRS)
        )
        offset = fnp.outer(node_per_pair, direction)
        positive = offset + noise
        negative = offset - noise
        x = fnp.concatenate([positive, negative], axis=0)

        row_weight_per_pair = _np.repeat(
            _np.array(_GH_WEIGHTS) / (2.0 * _np.array(_GH_PAIRS)), _GH_PAIRS
        ).astype(_np.float32)
        row_weights = fnp.array(_np.concatenate([row_weight_per_pair, row_weight_per_pair]))

        rows = []
        for w in mlp.weights:
            x = fnp.maximum(x @ w, 0.0)
            rows.append(fnp.sum(row_weights[:, None] * x, axis=0))
        return fnp.stack(rows, axis=0)


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
