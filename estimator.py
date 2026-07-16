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

import flopscope as flops
import flopscope.numpy as fnp
from whestbench import MLP, BaseEstimator

_COV_RESCALE_THRESHOLD = 1e100


class Estimator(BaseEstimator):
    def predict(self, mlp: MLP, budget: int) -> fnp.ndarray:
        """Radial-exact Monte Carlo, selected by B25.

        For z ~ N(0, I_d), z = r*u with r = ||z|| ~ chi(d), u = z/r ~
        Uniform(sphere), r independent of u. `MLP` has no bias field, so
        the ReLU forward pass is exactly positively homogeneous:
        f(c*x) = c*f(x) for c > 0. Hence E[f(z)] = E[r]*E[f(u)] exactly --
        substitute the closed-form E[r] for the sampled radius and
        forward only directions, eliminating the radial component of MC
        variance entirely at negligible extra FLOP cost.
        """
        n_samples = 6_500
        _ = budget
        width = mlp.width

        rng = fnp.random.default_rng(mlp.seed)
        z = rng.standard_normal((n_samples, width)).astype(fnp.float32)
        norms = fnp.linalg.norm(z, axis=1)
        u = z / norms[:, None]

        rows = []
        for w in mlp.weights:
            u = fnp.maximum(fnp.matmul(u, w), 0.0)
            rows.append(fnp.mean(u, axis=0))

        e_r = math.sqrt(2.0) * math.exp(
            math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
        )
        return e_r * fnp.stack(rows, axis=0)

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
