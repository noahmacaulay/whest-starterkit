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


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """B10: active-subspace Gauss-Hermite quadrature, single-batch forward pass.

        Same statistical estimator as the B1 experiment (soft-gate active
        direction via 4 power iterations, 16-node Gauss-Hermite quadrature
        along it, antithetic conditional draws in the orthogonal
        complement): B1 measured a genuine final-layer MSE improvement over
        the champion (7.995e-06 vs 8.505e-06) but lost the paired promotion
        gate because its `mean_effective_compute` was 28% higher even
        though its raw `flops_used` was within 0.4% of the champion's --
        the gap was call-overhead from 1,360 separate small matmuls (16
        nodes x pos/neg x 32 layers, plus power-iteration passes) versus
        the champion's 32 single full-batch matmuls (one per layer).

        This version builds one combined (~6,516, width) sample batch up
        front -- weighting each row by weight_i/(2*pairs_i) at aggregation
        time instead of averaging per node separately -- and forwards it
        through each layer with a single matmul call, matching the
        champion's call structure, to test whether the accuracy gain
        survives once the overhead artifact is removed.
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

        # --- dominant direction via 4 power iterations through the soft-gate Jacobian ---
        direction = fnp.ones(width)
        direction = direction / fnp.sqrt(fnp.sum(direction * direction))
        for _ in range(4):
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
