"""B22 block-orthogonal Gaussian Monte Carlo candidate."""

from __future__ import annotations

import numpy as _np
import flopscope.numpy as fnp
from whestbench import MLP, BaseEstimator


_N_SAMPLES = 6_500


def _block_orthogonal_normals(width: int, rng) -> fnp.ndarray:
    """Draw marginally standard-normal rows with orthogonal directions.

    A Haar-uniform direction times an independent chi(width) radius is exactly
    standard normal. Directions in each full block are mutually orthogonal,
    which provides space-filling negative dependence without changing any
    individual row's distribution.
    """
    full_blocks, remainder = divmod(_N_SAMPLES, width)
    blocks = []
    for _ in range(full_blocks):
        matrix = _np.asarray(rng.standard_normal((width, width)), dtype=_np.float64)
        q, r = _np.linalg.qr(matrix)
        signs = _np.sign(_np.diag(r))
        signs[signs == 0.0] = 1.0
        directions = (q * signs[None, :]).T
        radius_seed = _np.asarray(rng.standard_normal((width, width)), dtype=_np.float64)
        radii = _np.sqrt(_np.sum(radius_seed * radius_seed, axis=1))
        blocks.append(directions * radii[:, None])
    if remainder:
        blocks.append(
            _np.asarray(rng.standard_normal((remainder, width)), dtype=_np.float64)
        )
    return fnp.array(_np.concatenate(blocks, axis=0).astype(_np.float32))


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """Estimate all layer means with block-orthogonal Gaussian MC."""
        _ = budget
        rng = fnp.random.default_rng(mlp.seed)
        x = _block_orthogonal_normals(mlp.width, rng)
        rows = []
        for weight in mlp.weights:
            x = fnp.maximum(x @ weight, 0.0)
            rows.append(fnp.mean(x, axis=0))
        return fnp.stack(rows, axis=0)
