"""B14 active-subspace Gauss-Hermite candidate."""

from __future__ import annotations

import numpy as _np
import flopscope as flops
import flopscope.numpy as fnp
from whestbench import MLP, BaseEstimator


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
_GH_PAIRS = tuple(max(1, round(weight * 3_250)) for weight in _GH_WEIGHTS)


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """B14: B13's batched quadrature estimator without variance matmuls.

        The diagonal Gaussian-moment pass computes each variance as an exact
        elementwise reduction instead of a one-row matrix multiply.  This
        preserves the estimator while testing whether it avoids the remaining
        per-layer matmul tracing overhead.
        """
        _ = budget
        width = mlp.width

        mean = fnp.zeros(width)
        variance = fnp.ones(width)
        gains = []
        for weight in mlp.weights:
            pre_mean = weight.T @ mean
            pre_variance = fnp.maximum(
                fnp.sum((weight * weight) * variance[:, None], axis=0), 1e-12
            )
            sigma = fnp.sqrt(pre_variance)
            gain = flops.stats.norm.cdf(pre_mean / sigma)
            mean = pre_mean * gain + sigma * flops.stats.norm.pdf(pre_mean / sigma)
            second = ((pre_mean * pre_mean + pre_variance) * gain
                      + pre_mean * sigma * flops.stats.norm.pdf(pre_mean / sigma))
            variance = fnp.maximum(second - mean * mean, 1e-12)
            gains.append(gain)

        direction = fnp.ones(width)
        direction = direction / fnp.sqrt(fnp.sum(direction * direction))
        for _ in range(2):
            image = direction
            for weight, gain in zip(mlp.weights, gains):
                image = gain * (weight.T @ image)
            direction = image
            for weight, gain in zip(reversed(mlp.weights), reversed(gains)):
                direction = weight @ (gain * direction)
            direction = direction / fnp.sqrt(fnp.sum(direction * direction))

        total_pairs = sum(_GH_PAIRS)
        rng = fnp.random.default_rng(mlp.seed)
        noise = fnp.array(rng.standard_normal((total_pairs, width)).astype(fnp.float32))
        noise = noise - fnp.outer(noise @ direction, direction)

        node_per_pair = fnp.array(
            _np.repeat(_np.array(_GH_NODES, dtype=_np.float32), _GH_PAIRS)
        )
        offset = fnp.outer(node_per_pair, direction)
        x = fnp.concatenate([offset + noise, offset - noise], axis=0)

        row_weight_per_pair = _np.repeat(
            _np.array(_GH_WEIGHTS) / (2.0 * _np.array(_GH_PAIRS)), _GH_PAIRS
        ).astype(_np.float32)
        row_weights = fnp.array(
            _np.concatenate([row_weight_per_pair, row_weight_per_pair])
        )

        rows = []
        for weight in mlp.weights:
            x = fnp.maximum(x @ weight, 0.0)
            rows.append(fnp.sum(row_weights[:, None] * x, axis=0))
        return fnp.stack(rows, axis=0)
