"""Run one B35 calibration pass and persist it only after validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--class-name", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    args = parser.parse_args()

    if args.report.exists() or args.stderr.exists():
        raise SystemExit("refusing to overwrite an existing calibration artifact")

    command = [
        "uv",
        "run",
        "--frozen",
        "whest",
        "run",
        "--estimator",
        "candidate_gpt.py",
        "--class",
        args.class_name,
        "--runner",
        "subprocess",
        "--n-mlps",
        "10",
        "--detail",
        "raw",
        "--dataset",
        "hf://aicrowd/arc-whestbench-public-2026@v1-phase1",
        "--split",
        "mini",
        "--flop-budget",
        "272000000000",
        "--format",
        "json",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        print(completed.stderr)
        return completed.returncode

    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        print(f"JSON parse failed: {exc}")
        print(completed.stderr)
        return 2

    args.report.write_text(completed.stdout, encoding="utf-8")
    args.stderr.write_text(completed.stderr, encoding="utf-8")

    results = report["results"]
    n_mlps = report["run_config"]["n_mlps"]
    estimator_breakdown = results["breakdowns"]["estimator"]
    summary = {
        "class": args.class_name,
        "adjusted_final_layer_score": results["adjusted_final_layer_score"],
        "final_layer_mse": results["final_layer_mse"],
        "mean_effective_compute": results["mean_effective_compute"],
        "mean_flops_used": estimator_breakdown["flops_used"] / n_mlps,
        "mean_score_multiplier": results["mean_score_multiplier"],
        "failure_breakdown": results["failure_breakdown"],
        "report": str(args.report),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
