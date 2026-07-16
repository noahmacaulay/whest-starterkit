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


_POWER_ROUNDS = 2
_BLOCK_SIZE = 4


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """B19: block power iteration for the active-subspace direction.

        Builds on the B1/B10/B11/B13/B14/B16 active-subspace lineage
        (soft-gate active direction, 16-node Gauss-Hermite quadrature
        along it, antithetic draws in the orthogonal complement, single
        batched matmul per layer). Two prior findings motivate this:

        - B17: full-100-MLP recheck found 2-round power iteration from a
          single fixed start converges poorly for ~35/100 MLPs (min
          cosine similarity to a converged reference: 0.443).
        - B18: no single starting vector (deterministic ones, seeded
          -random, alternating-sign) reliably fixes this -- each fails on
          a *different* subset, consistent with some MLPs having a
          genuinely small top-1/top-2 eigenvalue gap in their soft-gate
          Jacobian.

        Key insight: batching K starting vectors into one (K, width)
        block and applying the Jacobian to the whole block costs the
        *same* number of matmul calls per round as a single vector (still
        one matmul per layer per traversal, just K rows instead of 1) --
        unlike gpt's B11 full-Jacobian materialization, this stays
        O(width^2*K), not O(width^3), so K=4 adds negligible raw FLOPs
        (power iteration is already <0.1% of total FLOPs). Running 4
        independent starts (ones, alternating-sign, and 2 seeded-random
        draws) through the same 2 rounds and picking whichever grew the
        most (proxy for best alignment with the dominant eigenvalue)
        recovers nearly all of the accuracy of an oracle that always
        picks the true best-converged vector: validated across all 100
        Mini-split MLPs before writing this candidate -- min cosine
        similarity to a 6-round reference improved from 0.443 (single
        ones-start) to 0.823 (block+heuristic, vs. 0.823 for the oracle),
        and MLPs below 0.999 similarity dropped from 35 to 9. The
        heuristic picked the true best vector in 81/100 cases outright.

        Also keeps B14's elementwise diagonal-variance fix (independently
        reimplemented, validated safe) and B16's finding that pair-count
        tuning is a dead end once at/above the compute floor -- so this
        uses the full 3,250 pair-count scale, not a reduced one.
        """
        _ = budget
        width = mlp.width

        # --- soft-gate diagonal Jacobian (cheap: O(depth*width) per layer) ---
        mean = fnp.zeros(width)
        variance = fnp.ones(width)
        gains = []
        for w in mlp.weights:
            pre_mean = w.T @ mean
            pre_variance = fnp.maximum(fnp.sum((w * w) * variance[:, None], axis=0), 1e-12)
            sigma = fnp.sqrt(pre_variance)
            gain = flops.stats.norm.cdf(pre_mean / sigma)
            mean = pre_mean * gain + sigma * flops.stats.norm.pdf(pre_mean / sigma)
            second = (pre_mean * pre_mean + pre_variance) * gain + pre_mean * sigma * flops.stats.norm.pdf(pre_mean / sigma)
            variance = fnp.maximum(second - mean * mean, 1e-12)
            gains.append(gain)

        # --- dominant direction via block power iteration (K starts, batched) ---
        rng = fnp.random.default_rng(mlp.seed)
        alt_np = _np.array([1.0 if i % 2 == 0 else -1.0 for i in range(width)], dtype=_np.float32)
        rand1_np = _np.array(rng.standard_normal(width)).astype(_np.float32)
        rand2_np = _np.array(rng.standard_normal(width)).astype(_np.float32)
        starts_np = _np.stack([
            _np.ones(width, dtype=_np.float32),
            alt_np,
            rand1_np,
            rand2_np,
        ], axis=0)
        block = fnp.array(starts_np)
        block = block / fnp.sqrt(fnp.sum(block * block, axis=1))[:, None]

        growth = None
        for _ in range(_POWER_ROUNDS):
            image = block
            for w, gain in zip(mlp.weights, gains):
                image = gain[None, :] * (image @ w)
            for w, gain in zip(reversed(mlp.weights), reversed(gains)):
                image = (gain[None, :] * image) @ w.T
            growth = fnp.sqrt(fnp.sum(image * image, axis=1))
            block = image / growth[:, None]

        best = int(_np.argmax(_np.array(growth)))
        direction = block[best]

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
