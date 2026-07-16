"""MSE/timing feasibility gate for B41 partial-Haar direction blocks."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import whestbench


DATASET = "hf://aicrowd/arc-whestbench-public-2026@v1-phase1"
DATASET_SHA256 = "5b00938b6bd809fe80acef08772c5654edf467863225ca9e304b76c779ecf433"
EXPERIMENT_ID = "B41-gpt-20260716T220957Z"
N_SAMPLES = 6_500
BLOCK_SIZES = (16, 32, 64, 128, 256)
CHAMPION_EFFECTIVE_COMPUTE = 3.004642329201e10
RESIDUAL_COMPUTE_PER_SECOND = 1.0e11
CLEAR_SCORE_RATIO = 0.98


def _seed(mlp_seed: int, repetition: int) -> int:
    if repetition == 0:
        return int(mlp_seed)
    sequence = np.random.SeedSequence([int(mlp_seed), repetition, 41])
    return int(sequence.generate_state(1, dtype=np.uint64)[0])


def _forward(mlp: whestbench.MLP, directions: np.ndarray) -> np.ndarray:
    x = directions
    for weight in mlp.weights:
        x = np.maximum(x @ np.asarray(weight), 0.0)
    e_r = math.sqrt(2.0) * math.exp(
        math.lgamma((mlp.width + 1) / 2.0) - math.lgamma(mlp.width / 2.0)
    )
    return e_r * np.mean(x, axis=0)


def _iid_directions(width: int, seed: int) -> tuple[np.ndarray, float]:
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((N_SAMPLES, width)).astype(np.float32)
    directions = z / np.linalg.norm(z, axis=1)[:, None]
    return directions, time.perf_counter() - start


def _partial_haar_directions(
    width: int, seed: int, block_size: int
) -> tuple[np.ndarray, float]:
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    k = min(block_size, width)
    n_blocks, remainder = divmod(N_SAMPLES, k)
    matrices = rng.standard_normal((n_blocks, width, k))
    q, r = np.linalg.qr(matrices, mode="reduced")
    signs = np.sign(np.diagonal(r, axis1=-2, axis2=-1))
    signs[signs == 0.0] = 1.0
    directions = np.transpose(q * signs[:, None, :], (0, 2, 1))
    directions = directions.reshape(n_blocks * k, width)
    if remainder:
        z = rng.standard_normal((remainder, width))
        z /= np.linalg.norm(z, axis=1)[:, None]
        directions = np.concatenate((directions, z), axis=0)
    return directions.astype(np.float32), time.perf_counter() - start


def _method_summary(rows: list[dict[str, float]]) -> dict[str, float]:
    generation_times = np.asarray([row["generation_time_s"] for row in rows])
    forward_times = np.asarray([row["forward_time_s"] for row in rows])
    return {
        "mean_mse": float(np.mean([row["mse"] for row in rows])),
        "median_generation_time_s": float(np.median(generation_times)),
        "mean_generation_time_s": float(np.mean(generation_times)),
        "median_forward_time_s": float(np.median(forward_times)),
        "mean_forward_time_s": float(np.mean(forward_times)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--n-mlps", type=int, default=10)
    parser.add_argument("--repetitions", type=int, default=4)
    args = parser.parse_args()
    if args.report.exists():
        raise SystemExit("refusing to overwrite an existing feasibility report")

    ds = whestbench.load_dataset(
        "aicrowd/arc-whestbench-public-2026",
        revision="v1-phase1",
        split="mini",
    )
    mlps = list(whestbench.iter_mlps(ds))
    methods = ["iid", *[f"haar_k{k}" for k in BLOCK_SIZES]]
    observations: dict[str, list[dict[str, float]]] = {
        method: [] for method in methods
    }
    per_mlp: list[dict[str, object]] = []

    for index in range(args.n_mlps):
        mlp = mlps[index]
        truth = np.asarray(ds[index]["final_means"], dtype=float)
        mlp_row: dict[str, object] = {
            "mlp_index": index,
            "mlp_name": ds[index]["mlp_name"],
            "methods": {},
        }
        for repetition in range(args.repetitions):
            seed = _seed(mlp.seed, repetition)
            for method in methods:
                if method == "iid":
                    directions, generation_time = _iid_directions(mlp.width, seed)
                else:
                    block_size = int(method.removeprefix("haar_k"))
                    directions, generation_time = _partial_haar_directions(
                        mlp.width, seed, block_size
                    )
                forward_start = time.perf_counter()
                prediction = _forward(mlp, directions)
                forward_time = time.perf_counter() - forward_start
                observations[method].append(
                    {
                        "mlp_index": index,
                        "repetition": repetition,
                        "seed": seed,
                        "mse": float(np.mean((prediction - truth) ** 2)),
                        "generation_time_s": generation_time,
                        "forward_time_s": forward_time,
                    }
                )

        method_rows: dict[str, dict[str, float]] = {}
        for method in methods:
            selected = [
                row for row in observations[method] if row["mlp_index"] == index
            ]
            method_rows[method] = _method_summary(selected)
        mlp_row["methods"] = method_rows
        per_mlp.append(mlp_row)

    aggregate = {method: _method_summary(observations[method]) for method in methods}
    iid = aggregate["iid"]
    for method in methods[1:]:
        row = aggregate[method]
        extra_generation_time = max(
            0.0,
            row["median_generation_time_s"] - iid["median_generation_time_s"],
        )
        estimated_compute = (
            CHAMPION_EFFECTIVE_COMPUTE
            + RESIDUAL_COMPUTE_PER_SECOND * extra_generation_time
        )
        row["mse_ratio_vs_iid"] = row["mean_mse"] / iid["mean_mse"]
        row["estimated_effective_compute"] = estimated_compute
        row["estimated_compute_ratio_vs_iid"] = (
            estimated_compute / CHAMPION_EFFECTIVE_COMPUTE
        )
        row["predicted_adjusted_score_ratio_vs_iid"] = (
            row["mse_ratio_vs_iid"] * row["estimated_compute_ratio_vs_iid"]
        )
    best_method = min(
        methods[1:],
        key=lambda method: aggregate[method][
            "predicted_adjusted_score_ratio_vs_iid"
        ],
    )
    best_ratio = aggregate[best_method]["predicted_adjusted_score_ratio_vs_iid"]
    aggregate["decision"] = {
        "best_method": best_method,
        "best_predicted_adjusted_score_ratio_vs_iid": best_ratio,
        "clear_score_ratio_threshold": CLEAR_SCORE_RATIO,
        "gate_pass": bool(best_ratio < CLEAR_SCORE_RATIO),
    }

    report = {
        "experiment_id": EXPERIMENT_ID,
        "dataset": DATASET,
        "dataset_sha256": DATASET_SHA256,
        "split": "mini",
        "indices": list(range(args.n_mlps)),
        "n_samples": N_SAMPLES,
        "repetitions": args.repetitions,
        "block_sizes": list(BLOCK_SIZES),
        "timing_model": {
            "champion_effective_compute": CHAMPION_EFFECTIVE_COMPUTE,
            "residual_compute_per_second": RESIDUAL_COMPUTE_PER_SECOND,
            "note": "Conservative lower bound: adds only median direction-generation time beyond iid; forward FLOPs are unchanged.",
        },
        "aggregate": aggregate,
        "per_mlp": per_mlp,
        "observations": observations,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
