"""Run or reproduce the approved Phase 1 study."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import torch

from .study import Phase1Study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/raw/LShape.mat")
    parser.add_argument("--output", default="runs/phase1-baseline")
    parser.add_argument("--checkpoint")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--context-mode", choices=["all", "window"], default="all")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output.resolve()/"matplotlib-cache"))
    torch.set_num_threads(2)
    study = Phase1Study.from_mat(args.data)
    if args.checkpoint:
        study.load_checkpoint(args.checkpoint)
    else:
        study.fit(output, epochs=args.epochs, verbose=True, context_mode=args.context_mode)
    demo_ids = [demo for demo in range(7) for _ in range(5)]
    seeds = [seed for _ in range(7) for seed in range(5)]
    start = time.perf_counter()
    result = study.rollout(study.points[demo_ids, :2], seeds=seeds)
    report = study.evaluate_rollouts(result["positions"], demo_ids, seeds)
    report["evaluation_seconds"] = time.perf_counter()-start
    (output/"evaluation.json").write_text(json.dumps(report, indent=2))
    torch.save(result, output/"rollouts.pt")
    from .visualization import plot_rollouts, plot_transport
    figure = plot_transport(study, output)
    plot_rollouts(study, result["positions"], demo_ids, output)
    source_files = sorted(Path(__file__).parent.glob("*.py"))
    checkpoint = Path(args.checkpoint) if args.checkpoint else output/"best.pt"
    manifest = {
        "source_path": study.source_path, "source_sha256": study.source_hash,
        "checkpoint": str(checkpoint.resolve()),
        "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "embedding_scale": study.scale,
        "split_unit": "recording/reference window; contexts kept together; overlapping recordings",
        "split_counts": {k: len(v) for k,v in study.splits.items()},
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "code_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        "torch": torch.__version__, "device": "cpu", "threads": 2,
        "prior_tangent_covariance": 0.5, "horizon": 8, "execute": 4, "integration_steps": 100,
        "context_mode": study.training_report.get("context_mode", "window"),
        "freeze_gate_passed": report["freeze_gate_passed"],
        "figure_rows": "validation and test conditioning windows, not model variants",
    }
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!="rollouts"}, indent=2), flush=True)
    print("Transport figure:", figure, flush=True)


if __name__ == "__main__":
    main()
