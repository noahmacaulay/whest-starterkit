"""B35 radial-exact estimators for affine effective-compute calibration."""

from __future__ import annotations

import math

import flopscope.numpy as fnp
from whestbench import BaseEstimator, MLP


class _RadialExactEstimator(BaseEstimator):
    """Run the champion algorithm at a configurable directional sample count."""

    n_samples = 6_500

    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        _ = budget
        width = mlp.width

        rng = fnp.random.default_rng(mlp.seed)
        z = rng.standard_normal((self.n_samples, width)).astype(fnp.float32)
        norms = fnp.linalg.norm(z, axis=1)
        u = z / norms[:, None]

        rows = []
        for weight in mlp.weights:
            u = fnp.maximum(fnp.matmul(u, weight), 0.0)
            rows.append(fnp.mean(u, axis=0))

        expected_radius = math.sqrt(2.0) * math.exp(
            math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
        )
        return expected_radius * fnp.stack(rows, axis=0)


class Estimator3250(_RadialExactEstimator):
    n_samples = 3_250


class Estimator6500(_RadialExactEstimator):
    n_samples = 6_500


class Estimator13000(_RadialExactEstimator):
    n_samples = 13_000


class Estimator26000(_RadialExactEstimator):
    n_samples = 26_000


class Estimator(Estimator26000):
    """B35 candidate: highest calibration sample count if feasibility passes."""
