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
_GH_PAIRS = tuple(max(1, round(w * 1_625)) for w in _GH_WEIGHTS)


_POWER_ITERATIONS = 2


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """B15: B13's active-subspace quadrature with a smaller main sample budget.

        Identical statistical estimator to B13/B10 (soft-gate active
        direction via 2 power iterations, 16-node Gauss-Hermite quadrature
        along it, antithetic draws in the orthogonal complement, single
        batched matmul per layer) except the main pair-count scale factor
        is 1,625 instead of 3,250, roughly halving the main sample budget
        (~6,500 -> ~3,250 total forward rows).

        Distinct from B14 (gpt's claimed item, batching the fixed-cost
        diagonal soft-gate calls): B13's aggregate flops_used (27.49e9)
        was already close to the champion's (27.35e9), while
        effective_compute (34.80e9) was ~7.3e9 higher -- consistent with a
        largely fixed per-call overhead from the 128 power-iteration + 32
        diagonal calls, independent of how many rows are in the single
        batched main-sampling matmul per layer. The 16-node quadrature
        gives *zero* sampling variance along the dominant direction --
        only the orthogonal-complement antithetic draws contribute MC
        noise -- so this estimator should be more sample-efficient per
        FLOP than plain MC (which has sampling variance in all 256
        dimensions), and halving the main budget should roughly halve the
        dominant raw-FLOP term while leaving the fixed overhead
        unchanged, netting a real effective_compute reduction even though
        MSE will increase somewhat from fewer orthogonal-complement draws.
        """
        _ = budget
        width = mlp.width

        # --- soft-gate diagonal Jacobian (cheap: O(depth*width) per layer) ---
        mean = fnp.zeros(width)
        variance = fnp.ones(width)
        gains = []
        for w in mlp.weights:
            pre_mean = w.T @ mean
            pre_variance = fnp.maximum((w * w).T @ variance, 1e-12)
            sigma = fnp.sqrt(pre_variance)
            gain = flops.stats.norm.cdf(pre_mean / sigma)
            mean = pre_mean * gain + sigma * flops.stats.norm.pdf(pre_mean / sigma)
            second = (pre_mean * pre_mean + pre_variance) * gain + pre_mean * sigma * flops.stats.norm.pdf(pre_mean / sigma)
            variance = fnp.maximum(second - mean * mean, 1e-12)
            gains.append(gain)

        # --- dominant direction via POWER_ITERATIONS power iterations ---
        direction = fnp.ones(width)
        direction = direction / fnp.sqrt(fnp.sum(direction * direction))
        for _ in range(_POWER_ITERATIONS):
            image = direction
            for w, gain in zip(mlp.weights, gains):
                image = gain * (w.T @ image)
            direction = image
            for w, gain in zip(reversed(mlp.weights), reversed(gains)):
                direction = w @ (gain * direction)
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
