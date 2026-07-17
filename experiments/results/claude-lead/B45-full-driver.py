"""B45: chunked resumable Full-split gate for the stacked candidate
(candidate_claude_lead.py = B43 exact-Haar directions + B42 chunked f32
forward).

Reuses B24/B26/B44's validated method: whestbench.cli._run_estimator_with_runner
driven directly over explicit index ranges of the immutable Full split,
ground truth read from the dataset's precomputed fields (never
recomputed), with the seed_protocol_version extracted from the ORIGINAL
unsliced dataset object BEFORE .select() (the weakref-metadata bug B26
caught and fixed). Usage:

    python B45-full-driver.py check                 # mandatory correctness check vs official CLI
    python B45-full-driver.py chunk 0 100 out0.json
    python B45-full-driver.py combine out*.json combined.json
"""
import sys
import json

REPO = r"C:\Users\dummy\Documents\code\whest_challenge\whest-claude-lead"
sys.path.insert(0, REPO)

import whestbench
from whestbench import MLP
from whestbench.scoring import ContestSpec, ContestData, _aggregate_budget_breakdowns
from whestbench.runner import SubprocessRunner, EstimatorEntrypoint
from whestbench.cli import _run_estimator_with_runner
from pathlib import Path
import flopscope.numpy as fnp

ESTIMATOR_PATH = Path(REPO) / "candidate_claude_lead.py"
DATASET_REPO = "aicrowd/arc-whestbench-public-2026"
REVISION = "v1-phase1"
FLOP_BUDGET = 272_000_000_000
LAMBDA = 1e11
WALL_TIME_LIMIT_S = 60.0


def build_report(split, start, end):
    import json as _json

    # IMPORTANT: extract seed_protocol_version from the metadata weakref
    # side-channel attached to the ORIGINAL (unsliced) dataset object
    # BEFORE calling .select() -- see B26's record for the bug this avoids
    # (silent fallback to seed_protocol_version "2.0" instead of "3.0",
    # corrupting MLP reconstruction with clean-looking flags).
    ds = whestbench.load_dataset(DATASET_REPO, revision=REVISION, split=split)
    md = whestbench.metadata(ds)
    proto_version = md["seed_protocol"]["version"]

    ds_slice = ds.select(range(start, end))
    n_mlps = len(ds_slice)

    spec = ContestSpec(
        width=256,
        depth=32,
        n_mlps=n_mlps,
        flop_budget=FLOP_BUDGET,
        ground_truth_samples=2_560_000,
        seed=None,
        wall_time_limit_s=WALL_TIME_LIMIT_S,
        residual_wall_time_limit_s=None,
        lambda_flops_per_second=LAMBDA,
    )

    mlps = [MLP.from_row(row, seed_protocol_version=proto_version) for row in ds_slice]
    all_layer_targets = [
        fnp.asarray(ds_slice[i]["all_layer_means"], dtype=fnp.float32) for i in range(n_mlps)
    ]
    final_targets = [
        fnp.asarray(ds_slice[i]["final_means"], dtype=fnp.float32) for i in range(n_mlps)
    ]
    avg_variances = [ds_slice[i]["avg_variance"] for i in range(n_mlps)]
    raw_breakdowns = ds_slice["sampling_budget_breakdown"][:n_mlps]
    breakdowns = [_json.loads(b) if isinstance(b, str) else b for b in raw_breakdowns]

    contest_data = ContestData(
        spec=spec,
        mlps=mlps,
        all_layer_targets=all_layer_targets,
        final_targets=final_targets,
        avg_variances=avg_variances,
        sampling_budget_breakdown=_aggregate_budget_breakdowns(breakdowns),
    )

    entrypoint = EstimatorEntrypoint(file_path=ESTIMATOR_PATH, class_name=None)
    runner = SubprocessRunner()

    report = _run_estimator_with_runner(
        runner,
        entrypoint=entrypoint,
        contest_spec=spec,
        n_mlps=n_mlps,
        profile=False,
        detail="raw",
        output_format="json",
        contest_data=contest_data,
    )
    return report


def cmd_check():
    print("Building chunked report for full[0:20]...", file=sys.stderr)
    report = build_report("full", 0, 20)
    print("full[0:20] aggregate final_layer_mse:", report["results"]["final_layer_mse"])
    print("full[0:20] aggregate mean_effective_compute:", report["results"]["mean_effective_compute"])

    print("Building chunked report for mini[0:30]...", file=sys.stderr)
    report2 = build_report("mini", 0, 30)
    print("mini[0:30] aggregate final_layer_mse:", report2["results"]["final_layer_mse"])
    print("mini[0:30] aggregate mean_effective_compute:", report2["results"]["mean_effective_compute"])


def cmd_chunk(start, end, outpath):
    report = build_report("full", start, end)
    with open(outpath, "w") as f:
        json.dump(report, f)
    print(f"wrote {outpath}: n_mlps={len(report['results']['per_mlp'])}", file=sys.stderr)
    print("aggregate final_layer_mse:", report["results"]["final_layer_mse"], file=sys.stderr)
    print("aggregate mean_effective_compute:", report["results"]["mean_effective_compute"], file=sys.stderr)
    failb = report["results"]["failure_breakdown"]
    print("failure_breakdown:", failb, file=sys.stderr)


def cmd_combine(paths, outpath):
    all_per_mlp = []
    for p in paths:
        with open(p) as f:
            d = json.load(f)
        all_per_mlp.extend(d["results"]["per_mlp"])

    # mlp_index is LOCAL to each chunk; mlp_name is the globally-unique
    # identity. Verify uniqueness on mlp_name, then reassign a global
    # mlp_index for the combined report.
    names = [r["mlp_name"] for r in all_per_mlp]
    assert len(names) == len(set(names)), "duplicate mlp_name across chunks!"
    n = len(all_per_mlp)
    for global_idx, r in enumerate(all_per_mlp):
        r["mlp_index"] = global_idx

    def mean(key):
        return sum(r[key] for r in all_per_mlp) / n

    final_layer_mse = mean("final_layer_mse")
    all_layers_mse = mean("all_layers_mse")
    adjusted_final_layer_score = mean("adjusted_final_layer_score")
    mean_effective_compute = mean("effective_compute")
    flops_used = mean("flops_used")
    mean_score_multiplier = max(0.1, mean_effective_compute / FLOP_BUDGET)

    depth = len(all_per_mlp[0]["per_layer_mse"])
    per_layer_mse = [
        sum(r["per_layer_mse"][i] for r in all_per_mlp) / n for i in range(depth)
    ]

    n_failed = sum(
        1 for r in all_per_mlp if r.get("budget_exhausted") or r.get("time_exhausted")
        or r.get("residual_wall_time_exhausted") or r.get("combined_budget_exhausted")
        or r.get("traceback")
    )
    failure_breakdown_simple = {
        "budget_exhausted": sum(1 for r in all_per_mlp if r.get("budget_exhausted")),
        "time_exhausted": sum(1 for r in all_per_mlp if r.get("time_exhausted")),
        "residual_wall_time_exhausted": sum(1 for r in all_per_mlp if r.get("residual_wall_time_exhausted")),
        "combined_budget_exhausted": sum(1 for r in all_per_mlp if r.get("combined_budget_exhausted")),
        "error": sum(1 for r in all_per_mlp if r.get("traceback")),
    }

    best = min(all_per_mlp, key=lambda r: r["adjusted_final_layer_score"])
    worst = max(all_per_mlp, key=lambda r: r["adjusted_final_layer_score"])

    combined = {
        "results": {
            "adjusted_final_layer_score": adjusted_final_layer_score,
            "final_layer_mse": final_layer_mse,
            "all_layers_mse": all_layers_mse,
            "per_layer_mse": per_layer_mse,
            "best_mlp_adjusted_final_layer_score": best["adjusted_final_layer_score"],
            "worst_mlp_adjusted_final_layer_score": worst["adjusted_final_layer_score"],
            "mean_score_multiplier": mean_score_multiplier,
            "mean_effective_compute": mean_effective_compute,
            "flops_used": flops_used,
            "n_failed_mlps": n_failed,
            "failure_breakdown": failure_breakdown_simple,
            "per_mlp": all_per_mlp,
        },
        "n_mlps_combined": n,
        "source_chunks": paths,
    }
    with open(outpath, "w") as f:
        json.dump(combined, f)
    print(f"wrote {outpath}: n={n}", file=sys.stderr)
    print("adjusted_final_layer_score:", adjusted_final_layer_score)
    print("final_layer_mse:", final_layer_mse)
    print("mean_effective_compute:", mean_effective_compute)
    print("flops_used:", flops_used)
    print("mean_score_multiplier:", mean_score_multiplier)
    print("failure_breakdown:", failure_breakdown_simple)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "check":
        cmd_check()
    elif cmd == "chunk":
        cmd_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif cmd == "combine":
        paths = sys.argv[2:-1]
        outpath = sys.argv[-1]
        cmd_combine(paths, outpath)
    else:
        raise SystemExit(f"unknown command {cmd}")
