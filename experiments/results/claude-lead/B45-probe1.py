"""B45 probe 1: prediction agreement and residual decomposition.

Checks on 3 real Mini MLPs that the B45 candidate (B43 directions + B42
chunked f32 forward) reproduces the B43 candidate's predictions within
float32 forward rounding (B42 precedent: ~1e-7 absolute), and compares
their in-process charged-residual decompositions.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

import flopscope as flops
import flopscope.numpy as fnp
from whestbench.dataset import load_dataset, mlp_at

BUDGET = 272_000_000_000
ROOT = Path(__file__).resolve().parents[3]


def load_estimator(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Estimator()


def run_once(est, mlp):
    ctx = flops.BudgetContext(flop_budget=BUDGET, quiet=True)
    with ctx:
        pred = est.predict(mlp, BUDGET)
    return pred, {
        "flops": ctx.flops_used,
        "wall": ctx.wall_time_s,
        "backend": ctx.flopscope_backend_time_s,
        "overhead": ctx.flopscope_overhead_time_s,
        "residual": ctx.residual_wall_time_s,
    }


def main():
    b43 = load_estimator(str(ROOT / "candidate_claude.py"))
    b45 = load_estimator(str(ROOT / "candidate_claude_lead.py"))
    champ = load_estimator(str(ROOT / "estimator.py"))

    ds = load_dataset("aicrowd/arc-whestbench-public-2026", revision="v1-phase1", split="mini")
    for idx in (0, 1, 2):
        mlp = mlp_at(ds, idx)
        # warm each estimator once on this MLP before measuring
        for est in (b43, b45, champ):
            run_once(est, mlp)
        p43, s43 = run_once(b43, mlp)
        p45, s45 = run_once(b45, mlp)
        pch, sch = run_once(champ, mlp)
        diff = float(fnp.max(fnp.abs(p45 - p43)))
        diff_final = float(fnp.max(fnp.abs(p45[-1] - p43[-1])))
        print(f"MLP {idx} ({mlp.seed}):", flush=True)
        print(f"  max|B45-B43| all layers = {diff:.3e}   final layer = {diff_final:.3e}")
        for name, s in (("B43", s43), ("B45", s45), ("champ(B42)", sch)):
            eff = s["flops"] + 1e11 * s["residual"]
            print(
                f"  {name:>10}: flops={s['flops']:.5g} residual={s['residual']*1e3:6.2f}ms "
                f"effective={eff:.5g} mult={max(0.1, eff/BUDGET):.4f}"
            )
        sys.stdout.flush()


if __name__ == "__main__":
    main()
