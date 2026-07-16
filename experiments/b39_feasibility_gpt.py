"""Bias/variance feasibility gate for B39 structured orthogonal directions."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import whestbench


DATASET = "hf://aicrowd/arc-whestbench-public-2026@v1-phase1"
DATASET_SHA256 = "5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433"
EXPERIMENT_ID = "B39-gpt-20260716T205516Z"
N_SAMPLES = 6_500


def _seed(mlp_seed: int, repetition: int) -> int:
    if repetition == 0:
        return int(mlp_seed)
    sequence = np.random.SeedSequence([int(mlp_seed), repetition, 39])
    return int(sequence.generate_state(1, dtype=np.uint64)[0])


def _forward(mlp: whestbench.MLP, directions: np.ndarray) -> np.ndarray:
    x = directions
    for weight in mlp.weights:
        x = np.maximum(x @ np.asarray(weight), 0.0)
    e_r = math.sqrt(2.0) * math.exp(
        math.lgamma((mlp.width + 1) / 2.0) - math.lgamma(mlp.width / 2.0)
    )
    return e_r * np.mean(x, axis=0)


def radial_iid(mlp: whestbench.MLP, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((N_SAMPLES, mlp.width)).astype(np.float32)
    return _forward(mlp, z / np.linalg.norm(z, axis=1)[:, None])


def structured_orthogonal(mlp: whestbench.MLP, seed: int) -> np.ndarray:
    width = mlp.width
    rng = np.random.default_rng(seed)
    n_blocks, remainder = divmod(N_SAMPLES, width)
    q = np.broadcast_to(
        np.eye(width, dtype=np.float32), (n_blocks, width, width)
    ).copy()
    for _stage in range(3):
        step = 1
        while step < width:
            shaped = q.reshape(n_blocks, width, -1, 2, step)
            left = shaped[..., 0, :]
            right = shaped[..., 1, :]
            q = np.concatenate((left + right, left - right), axis=-1)
            q = q.reshape(n_blocks, width, width)
            step *= 2
        q /= math.sqrt(width)
        signs = rng.standard_normal((n_blocks, width)).astype(np.float32)
        q *= np.where(signs >= 0.0, 1.0, -1.0).astype(np.float32)[:, None, :]
    directions = q.reshape(n_blocks * width, width)
    if remainder:
        z = rng.standard_normal((remainder, width)).astype(np.float32)
        z /= np.linalg.norm(z, axis=1)[:, None]
        directions = np.concatenate((directions, z), axis=0)
    return _forward(mlp, directions)


def summarize(predictions: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    mean_prediction = np.mean(predictions, axis=0)
    seed_variance = float(np.mean(np.var(predictions, axis=0, ddof=1)))
    raw_ensemble_bias2 = float(np.mean((mean_prediction - truth) ** 2))
    corrected_bias2 = raw_ensemble_bias2 - seed_variance / predictions.shape[0]
    return {
        "mean_rep_mse": float(np.mean((predictions - truth[None, :]) ** 2)),
        "seed_variance": seed_variance,
        "raw_ensemble_bias2": raw_ensemble_bias2,
        "corrected_bias2": corrected_bias2,
        "estimated_expected_mse": seed_variance + max(corrected_bias2, 0.0),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--n-mlps", type=int, default=10)
    parser.add_argument("--repetitions", type=int, default=6)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit("refusing to overwrite an existing feasibility report")

    ds = whestbench.load_dataset(
        "aicrowd/arc-whestbench-public-2026",
        revision="v1-phase1",
        split="mini",
    )
    mlps = list(whestbench.iter_mlps(ds))
    per_mlp = []
    for index in range(args.n_mlps):
        mlp = mlps[index]
        truth = np.asarray(ds[index]["final_means"], dtype=float)
        seeds = [_seed(mlp.seed, rep) for rep in range(args.repetitions)]
        iid = np.stack([radial_iid(mlp, seed) for seed in seeds]).astype(float)
        structured = np.stack(
            [structured_orthogonal(mlp, seed) for seed in seeds]
        ).astype(float)
        iid_summary = summarize(iid, truth)
        structured_summary = summarize(structured, truth)
        per_mlp.append(
            {
                "mlp_index": index,
                "mlp_name": ds[index]["mlp_name"],
                "seeds": seeds,
                "iid": iid_summary,
                "structured": structured_summary,
                "rep_mse_relative_change": (
                    structured_summary["mean_rep_mse"]
                    / iid_summary["mean_rep_mse"]
                    - 1.0
                ),
            }
        )

    aggregate = {}
    for method in ("iid", "structured"):
        aggregate[method] = {
            key: float(np.mean([row[method][key] for row in per_mlp]))
            for key in per_mlp[0][method]
        }
    aggregate["rep_mse_relative_change"] = (
        aggregate["structured"]["mean_rep_mse"]
        / aggregate["iid"]["mean_rep_mse"]
        - 1.0
    )
    aggregate["seed_variance_relative_change"] = (
        aggregate["structured"]["seed_variance"]
        / aggregate["iid"]["seed_variance"]
        - 1.0
    )
    aggregate["structured_bias2_over_iid_expected_mse"] = (
        max(aggregate["structured"]["corrected_bias2"], 0.0)
        / aggregate["iid"]["estimated_expected_mse"]
    )
    aggregate["gate_pass"] = bool(
        aggregate["structured"]["estimated_expected_mse"]
        < aggregate["iid"]["estimated_expected_mse"]
        and aggregate["rep_mse_relative_change"] < 0.0
    )

    report = {
        "experiment_id": EXPERIMENT_ID,
        "dataset": DATASET,
        "dataset_sha256": DATASET_SHA256,
        "split": "mini",
        "indices": list(range(args.n_mlps)),
        "n_samples": N_SAMPLES,
        "repetitions": args.repetitions,
        "design": "25 H-D-H-D-H-D orthogonal blocks plus 100 iid directions",
        "aggregate": aggregate,
        "per_mlp": per_mlp,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
