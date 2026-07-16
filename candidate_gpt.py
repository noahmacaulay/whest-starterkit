"""Your estimator. Edit `predict()`. Run `python estimator.py` to iterate.

Stage 1 of the WhestBench ladder: just `flopscope` and the local engine. No CLI
knowledge required. Once `predict()` returns something interesting, climb to
Stage 2: `whest validate --estimator estimator.py`.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import flopscope as flops
import flopscope.numpy as fnp
from whestbench import MLP, BaseEstimator

_COV_RESCALE_THRESHOLD = 1e100


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """Diagonal plus adaptively truncated low-rank covariance recursion."""
        _ = budget
        width = mlp.width
        rng = fnp.random.default_rng(mlp.seed)
        mean = fnp.zeros(width)
        diagonal = fnp.ones(width)
        factors = fnp.zeros((width, 1))
        rows = []
        for layer, w in enumerate(mlp.weights):
            # Represent the activation covariance as diag(diagonal) + U U^T.
            # The leading eigendirections of the next covariance are recovered
            # by deflated power iterations without materializing a dense matrix.
            diagonal_pre = (w * w).T @ diagonal
            factors_pre = w.T @ factors
            variance_pre = diagonal_pre + fnp.sum(factors_pre * factors_pre, axis=1)
            mean_pre = w.T @ mean
            sigma_pre = fnp.sqrt(fnp.maximum(variance_pre, 1e-12))
            alpha = mean_pre / sigma_pre
            gate = flops.stats.norm.cdf(alpha)
            density = flops.stats.norm.pdf(alpha)
            mean = mean_pre * gate + sigma_pre * density
            second = (mean_pre * mean_pre + variance_pre) * gate + mean_pre * sigma_pre * density
            variance_post = fnp.maximum(second - mean * mean, 0.0)

            # The stored spectrum becomes sharply concentrated in deep layers;
            # use a larger cap while it is diffuse and an eigenvalue cutoff to
            # adapt the retained rank to this particular MLP and layer.
            rank_cap = 16 if layer < 8 else (8 if layer < 16 else 4)
            trace_pre = fnp.maximum(fnp.sum(variance_pre), 1e-12)
            selected = []
            for _ in range(rank_cap):
                vector = fnp.array(rng.standard_normal(width).astype(fnp.float32))
                for _ in range(3):
                    product = w.T @ (diagonal * (w @ vector))
                    product = product + factors_pre @ (factors_pre.T @ vector)
                    for direction in selected:
                        product = product - direction * fnp.sum(direction * product)
                    vector = product / fnp.sqrt(fnp.maximum(fnp.sum(product * product), 1e-12))
                product = w.T @ (diagonal * (w @ vector))
                product = product + factors_pre @ (factors_pre.T @ vector)
                for direction in selected:
                    product = product - direction * fnp.sum(direction * product)
                eigenvalue = fnp.maximum(fnp.sum(vector * product), 0.0)
                # Components under 0.5% of total variance are discarded.
                keep = eigenvalue >= 0.005 * trace_pre
                selected.append(fnp.where(keep, vector * fnp.sqrt(eigenvalue), fnp.zeros(width)))
            factors = gate[:, None] * fnp.stack(selected, axis=1)
            diagonal = fnp.maximum(variance_post - fnp.sum(factors * factors, axis=1), 1e-12)
            rows.append(mean)
        return fnp.stack(rows, axis=0)

        # --- Step 1: initialise the input distribution ---
        # Input is modelled as standard multivariate normal: mu=0, cov=I.
        mu = fnp.zeros(width)  # shape (width,)
        cov = fnp.eye(width)  # shape (width, width)
        log_scale = 0.0  # tracks accumulated log of rescaling factor

        rows = []
        for w in mlp.weights:  # w has shape (width, width)
            # --- Step 2: overflow prevention ---
            # If the covariance has grown very large, rescale (mu, cov) by the
            # square root of the largest variance so that downstream matmuls
            # stay in a safe range.  We compensate in the recorded mean later.
            cov_diag = fnp.diag(cov)
            max_var_np = float(fnp.max(cov_diag))
            if max_var_np > _COV_RESCALE_THRESHOLD:
                s = float(fnp.sqrt(max_var_np))
                mu = mu / s
                cov = cov / (s * s)
                log_scale += float(fnp.log(s))

            # --- Step 3: propagate through the linear layer ---
            # Pre-activation mean:         mu_pre  = W^T mu
            # Pre-activation covariance:   cov_pre = W^T cov W
            #
            # Use einsum (not the chained matmul `w.T @ cov @ w`) so flopscope
            # detects that the two `w` operands are the same tensor and tags
            # cov_pre as symmetric. Symmetry then flows through the post-ReLU
            # outer-product update below (line ~140), so the resulting `cov`
            # is also tagged symmetric — no SymmetryLossWarning to suppress.
            # See https://github.com/AIcrowd/whestbench/issues/27 for the
            # background.
            mu_pre = w.T @ mu
            cov_pre = fnp.einsum("ij,ia,jb->ab", cov, w, w)

            # Extract per-neuron pre-activation standard deviations from the
            # diagonal of cov_pre.
            var_pre = fnp.maximum(fnp.diag(cov_pre), 1e-12)
            sigma_pre = fnp.sqrt(var_pre)

            # --- Step 4: compute alpha = mu / sigma for each neuron ---
            alpha = mu_pre / sigma_pre
            phi_alpha = flops.stats.norm.pdf(alpha)
            Phi_alpha = flops.stats.norm.cdf(alpha)

            # --- Step 5: post-ReLU mean (exact per neuron) ---
            # E[ReLU(pre)] = mu_pre * Phi(alpha) + sigma_pre * phi(alpha)
            mu = mu_pre * Phi_alpha + sigma_pre * phi_alpha

            # --- Step 6: post-ReLU diagonal variance (exact per neuron) ---
            # E[z^2] = (mu_pre^2 + var_pre) * Phi(alpha) + mu_pre * sigma_pre * phi(alpha)
            ez2 = (mu_pre * mu_pre + var_pre) * Phi_alpha + mu_pre * sigma_pre * phi_alpha
            var_post = fnp.maximum(ez2 - mu * mu, 0.0)

            # --- Step 7: approximate post-ReLU covariance ---
            # gain[i] = Phi(alpha[i])  when sigma_pre[i] > 0, else 0
            sigma_np = fnp.asarray(sigma_pre, dtype=fnp.float64)
            Phi_np = fnp.asarray(Phi_alpha, dtype=fnp.float64)
            gain_np = fnp.where(sigma_np > 1e-12, Phi_np, 0.0)
            gain = fnp.array(gain_np.astype(fnp.float32))

            # Off-diagonal approximation:  cov_post[i,j] ≈ gain[i]*gain[j]*cov_pre[i,j]
            cov = fnp.multiply(fnp.outer(gain, gain), cov_pre)

            # Replace the diagonal with the exact marginal variances.
            fnp.fill_diagonal(cov, var_post)

            # --- Step 8: record mean in original (unscaled) coordinates ---
            scale_factor = float(fnp.exp(log_scale))
            rows.append(mu * scale_factor)

        # Stack all layer means into a single (depth, width) array
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
