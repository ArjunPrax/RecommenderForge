"""Command line entry points for the control plane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ledger import ExperimentLedger
from .qualification import run_qualification
from .reporting import write_report
from .baseline_runner import run_safe_numpy_fm
from .torch_fm import run_safe_torch_fm
from .ranking_fm import RankingFMConfig, run_ranking_fm
from .autonomous import run_autonomous_history, run_autonomous_multitask, run_autonomous_ranking
from .submission import generate_submission


def main() -> None:
    parser = argparse.ArgumentParser(prog="tiktok-ml-agent")
    commands = parser.add_subparsers(dest="command", required=True)
    qualification = commands.add_parser("qualification", help="run deterministic autonomous-loop qualification")
    qualification.add_argument("--output-dir", type=Path, default=Path("artifacts/qualification"))
    report = commands.add_parser("report", help="render a report from an existing ledger")
    report.add_argument("--ledger", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    baseline = commands.add_parser("baseline-valid", help="run one organizer FM seed on train/validation only")
    baseline.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    baseline.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    baseline.add_argument("--seed", type=int, default=0)
    torch_baseline = commands.add_parser("torch-baseline-valid", help="run one PyTorch pointwise FM seed on train/validation only")
    torch_baseline.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    torch_baseline.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    torch_baseline.add_argument("--seed", type=int, default=0)
    ranking = commands.add_parser("ranking-valid", help="run a train/validation-only ranking FM seed")
    ranking.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    ranking.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    ranking.add_argument("--seed", type=int, default=0)
    ranking.add_argument("--objective", choices=("bpr", "listwise"), required=True)
    ranking.add_argument("--history-cross", action="store_true", help="add strictly-earlier long-view history as an FM cross field")
    autonomous_ranking = commands.add_parser(
        "autonomous-ranking", help="plan and run the initial checkpoint-backed ranking-objective batch"
    )
    autonomous_ranking.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_ranking.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_ranking.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_ranking.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-ranking"))
    autonomous_history = commands.add_parser("autonomous-history", help="run the checkpoint-parented temporal-history candidate")
    autonomous_history.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_history.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_history.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_history.add_argument("--parent-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_history.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-history"))
    autonomous_multitask = commands.add_parser("autonomous-multitask", help="run the checkpoint-parented multi-feedback candidate")
    autonomous_multitask.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_multitask.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_multitask.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_multitask.add_argument("--parent-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_multitask.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-multitask"))
    submission = commands.add_parser("submission", help="generate a CSV from one frozen checkpoint manifest")
    submission.add_argument("--ledger", type=Path, required=True)
    submission.add_argument("--run-id", required=True)
    submission.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    submission.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    submission.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "qualification":
        print(json.dumps(run_qualification(args.output_dir), indent=2, sort_keys=True))
    elif args.command == "report":
        ledger = ExperimentLedger(args.ledger)
        try:
            print(write_report(ledger, args.output))
        finally:
            ledger.close()
    elif args.command == "baseline-valid":
        print(json.dumps(run_safe_numpy_fm(args.starter_kit, args.data_dir, args.seed), indent=2, sort_keys=True))
    elif args.command == "torch-baseline-valid":
        print(json.dumps(run_safe_torch_fm(args.starter_kit, args.data_dir, args.seed), indent=2, sort_keys=True))
    elif args.command == "ranking-valid":
        config = RankingFMConfig(objective=args.objective, history_cross=args.history_cross)
        print(json.dumps(run_ranking_fm(args.starter_kit, args.data_dir, args.seed, config), indent=2, sort_keys=True))
    elif args.command == "autonomous-ranking":
        print(
            json.dumps(
                run_autonomous_ranking(
                    repository_root=args.repository_root,
                    starter_kit_dir=args.starter_kit,
                    data_dir=args.data_dir,
                    output_dir=args.output_dir,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "autonomous-history":
        print(
            json.dumps(
                run_autonomous_history(
                    repository_root=args.repository_root,
                    starter_kit_dir=args.starter_kit,
                    data_dir=args.data_dir,
                    parent_ledger_path=args.parent_ledger,
                    output_dir=args.output_dir,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "autonomous-multitask":
        print(json.dumps(run_autonomous_multitask(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, parent_ledger_path=args.parent_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "submission":
        print(generate_submission(ledger_path=args.ledger, run_id=args.run_id, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, output_path=args.output))


if __name__ == "__main__":
    main()
