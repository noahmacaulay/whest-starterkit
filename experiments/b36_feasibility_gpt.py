"""Feasibility check for B36 output-template projection on public Mini MLPs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import whestbench


DATASET = "hf://aicrowd/arc-whestbench-public-2026@v1-phase1"


def radial_mc(mlp: whestbench.MLP, n_samples: int = 6_500) -> np.ndarray:
    width = mlp.width
    rng = np.random.default_rng(mlp.seed)
    z = rng.standard_normal((n_samples, width)).astype(np.float32)
    u = z / np.linalg.norm(z, axis=1)[:, None]
    rows = []
    for weight in mlp.weights:
        u = np.maximum(u @ np.asarray(weight), 0.0)
        rows.append(np.mean(u, axis=0))
    e_r = math.sqrt(2.0) * math.exp(
        math.lgamma((width + 1) / 2.0) - math.lgamma(width / 2.0)
    )
    return e_r * np.stack(rows)


def covariance_template(mlp: whestbench.MLP) -> np.ndarray:
    width = mlp.width
    mu = np.zeros(width)
    cov = np.eye(width)
    normal = NormalDist()
    for weight in mlp.weights:
        w = np.asarray(weight)
        mu_pre = w.T @ mu
        cov_pre = w.T @ cov @ w
        var_pre = np.maximum(np.diag(cov_pre), 1e-12)
        sigma_pre = np.sqrt(var_pre)
        alpha = mu_pre / sigma_pre
        phi = np.exp(-0.5 * alpha * alpha) / math.sqrt(2.0 * math.pi)
        Phi = np.fromiter((normal.cdf(float(x)) for x in alpha), dtype=float)
        mu = mu_pre * Phi + sigma_pre * phi
        ez2 = (mu_pre * mu_pre + var_pre) * Phi + mu_pre * sigma_pre * phi
        var_post = np.maximum(ez2 - mu * mu, 0.0)
        cov = np.outer(Phi, Phi) * cov_pre
        np.fill_diagonal(cov, var_post)
    return mu


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--n-mlps", type=int, default=10)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit("refusing to overwrite an existing feasibility report")

    ds = whestbench.load_dataset(DATASET, split="mini")
    mlps = list(whestbench.iter_mlps(ds))
    per_mlp = []
    for index in range(args.n_mlps):
        mlp = mlps[index]
        truth = np.asarray(ds[index]["final_means"], dtype=float)
        mc = np.asarray(radial_mc(mlp)[-1], dtype=float)
        template = covariance_template(mlp)
        energy = float(template @ template)
        fitted_scale = max(float(mc @ template) / energy, 0.0)
        oracle_scale = max(float(truth @ template) / energy, 0.0)
        projected = fitted_scale * template
        oracle_projected = oracle_scale * template
        per_mlp.append(
            {
                "mlp_index": index,
                "mlp_name": ds[index]["mlp_name"],
                "mc_mse": float(np.mean((mc - truth) ** 2)),
                "projected_mse": float(np.mean((projected - truth) ** 2)),
                "oracle_projected_mse": float(
                    np.mean((oracle_projected - truth) ** 2)
                ),
                "template_direction_cosine": float(
                    (truth @ template)
                    / math.sqrt(float(truth @ truth) * energy)
                ),
                "fitted_scale": fitted_scale,
                "oracle_scale": oracle_scale,
            }
        )

    mean_mc = float(np.mean([row["mc_mse"] for row in per_mlp]))
    mean_projected = float(np.mean([row["projected_mse"] for row in per_mlp]))
    mean_oracle = float(
        np.mean([row["oracle_projected_mse"] for row in per_mlp])
    )
    report = {
        "experiment_id": "B36-gpt-20260716T180943Z",
        "dataset": DATASET,
        "dataset_sha256": "5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433",
        "split": "mini",
        "indices": list(range(args.n_mlps)),
        "n_samples": 6500,
        "mean_mc_mse": mean_mc,
        "mean_projected_mse": mean_projected,
        "mean_oracle_projected_mse": mean_oracle,
        "projected_relative_change": mean_projected / mean_mc - 1.0,
        "oracle_bias_floor_relative_to_mc": mean_oracle / mean_mc,
        "per_mlp": per_mlp,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
