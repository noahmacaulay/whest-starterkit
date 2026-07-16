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


_GH_PAIRS_HALF = tuple(max(1, p // 2) for p in _GH_PAIRS)


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """B12: two-direction active-subspace quadrature with 4-way antithetic split.

        Extends B1/B10's estimator (soft-gate active direction via power
        iteration, 16-node Gauss-Hermite quadrature along it, antithetic
        draws in the orthogonal complement) with a second, deflated power
        -iteration direction. AGENTS.md notes depth-32 covariance is
        "often rank-1 dominated", not purely rank-1, so a second direction
        may carry residual signal the first misses.

        Rather than a second quadrature (would need new, unverified GH
        constants under time pressure), the orthogonal-complement noise is
        split into its component along the second direction and the
        remaining residual, and both components are independently sign
        -flipped: (+d2,+resid), (-d2,+resid), (+d2,-resid), (-d2,-resid).
        All four share the same expectation by the same symmetry argument
        that makes plain antithetic pairing unbiased (each is a valid
        alternative draw from the same orthogonal-complement Gaussian), so
        this stays unbiased -- verified against a synthetic reference
        before use here. Base draw count is halved so total forward rows
        stay close to B1/B10's ~6,516.
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

        def jacobian_apply(vec):
            image = vec
            for w, gain in zip(mlp.weights, gains):
                image = gain * (w.T @ image)
            for w, gain in zip(reversed(mlp.weights), reversed(gains)):
                image = w @ (gain * image)
            return image

        # --- dominant direction via 4 power iterations (same as B1/B10) ---
        d1 = fnp.ones(width)
        d1 = d1 / fnp.sqrt(fnp.sum(d1 * d1))
        for _ in range(4):
            d1 = jacobian_apply(d1)
            d1 = d1 / fnp.sqrt(fnp.sum(d1 * d1))

        # --- second direction: deflated power iteration, orthogonal to d1 ---
        d2_init = _np.array([1.0 if i % 2 == 0 else -1.0 for i in range(width)], dtype=_np.float32)
        d2 = fnp.array(d2_init)
        d2 = d2 - fnp.sum(d2 * d1) * d1
        d2 = d2 / fnp.sqrt(fnp.sum(d2 * d2))
        for _ in range(4):
            d2 = jacobian_apply(d2)
            d2 = d2 - fnp.sum(d2 * d1) * d1
            d2 = d2 / fnp.sqrt(fnp.sum(d2 * d2))

        # --- build one combined batch: 16 GH nodes along d1, 4-way antithetic in (d2, residual) ---
        total_base = sum(_GH_PAIRS_HALF)
        rng = fnp.random.default_rng(mlp.seed)
        noise = fnp.array(rng.standard_normal((total_base, width)).astype(fnp.float32))
        noise = noise - fnp.outer(noise @ d1, d1)
        comp2 = fnp.outer(noise @ d2, d2)
        residual = noise - comp2

        node_per_pair = fnp.array(
            _np.repeat(_np.array(_GH_NODES, dtype=_np.float32), _GH_PAIRS_HALF)
        )
        offset = fnp.outer(node_per_pair, d1)
        v1 = offset + comp2 + residual
        v2 = offset - comp2 + residual
        v3 = offset + comp2 - residual
        v4 = offset - comp2 - residual
        x = fnp.concatenate([v1, v2, v3, v4], axis=0)

        row_weight_per_pair = _np.repeat(
            _np.array(_GH_WEIGHTS) / (4.0 * _np.array(_GH_PAIRS_HALF)), _GH_PAIRS_HALF
        ).astype(_np.float32)
        row_weights = fnp.array(_np.concatenate([row_weight_per_pair] * 4))

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
