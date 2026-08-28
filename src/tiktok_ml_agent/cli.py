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
from .autonomous import run_autonomous_backbone, run_autonomous_ensemble, run_autonomous_history, run_autonomous_lambda_ranking, run_autonomous_multitask, run_autonomous_negative_sampling, run_autonomous_ranking, run_autonomous_temporal, run_autonomous_three_ensemble, run_autonomous_watchtime
from .submission import generate_submission
from .scale import ScaleArtifactAdapter, write_preflight
from .scale_baseline import run_streaming_popularity
from .campaign import write_campaign_report
from .finalization import designate_final


def main() -> None:
    parser = argparse.ArgumentParser(prog="tiktok-ml-agent")
    commands = parser.add_subparsers(dest="command", required=True)
    qualification = commands.add_parser("qualification", help="run deterministic autonomous-loop qualification")
    qualification.add_argument("--output-dir", type=Path, default=Path("artifacts/qualification"))
    report = commands.add_parser("report", help="render a report from an existing ledger")
    report.add_argument("--ledger", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    campaign = commands.add_parser("campaign-status", help="materialize convergence evidence from declared ledger runs")
    campaign.add_argument("--campaign", type=Path, required=True, help="JSON campaign configuration with explicit ledger/run references")
    campaign.add_argument("--output", type=Path, required=True)
    finalization = commands.add_parser("designate-final", help="bind a converged campaign's frozen best checkpoint as designated final")
    finalization.add_argument("--campaign-report", type=Path, required=True)
    finalization.add_argument("--final-ledger", type=Path, required=True)
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
    autonomous_watchtime = commands.add_parser("autonomous-watchtime", help="run the train-only watch-completion BPR candidate")
    autonomous_watchtime.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_watchtime.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_watchtime.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_watchtime.add_argument("--parent-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_watchtime.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-watchtime"))
    autonomous_sampling = commands.add_parser("autonomous-negative-sampling", help="run the denser same-user BPR negative-sampling candidate")
    autonomous_sampling.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_sampling.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_sampling.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_sampling.add_argument("--parent-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_sampling.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-negative-sampling"))
    autonomous_lambda = commands.add_parser("autonomous-lambda-ranking", help="run the top-five-aware Lambda-BPR candidate")
    autonomous_lambda.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_lambda.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_lambda.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_lambda.add_argument("--parent-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_lambda.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-lambda-ranking"))
    autonomous_ensemble = commands.add_parser("autonomous-ensemble", help="evaluate a frozen-component rank ensemble")
    autonomous_ensemble.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_ensemble.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_ensemble.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_ensemble.add_argument("--bpr-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_ensemble.add_argument("--history-ledger", type=Path, default=Path("artifacts/autonomous-history-verified/ledger.sqlite"))
    autonomous_ensemble.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-ensemble"))
    autonomous_temporal = commands.add_parser("autonomous-temporal", help="run the inference-known temporal cross candidate")
    autonomous_temporal.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_temporal.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_temporal.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_temporal.add_argument("--parent-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_temporal.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-temporal"))
    autonomous_three_ensemble = commands.add_parser("autonomous-three-ensemble", help="evaluate a three-component frozen rank ensemble")
    autonomous_three_ensemble.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_three_ensemble.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_three_ensemble.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_three_ensemble.add_argument("--bpr-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_three_ensemble.add_argument("--history-ledger", type=Path, default=Path("artifacts/autonomous-history-verified/ledger.sqlite"))
    autonomous_three_ensemble.add_argument("--temporal-ledger", type=Path, default=Path("artifacts/autonomous-temporal/ledger.sqlite"))
    autonomous_three_ensemble.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-three-ensemble"))
    autonomous_backbone = commands.add_parser("autonomous-backbone", help="run the compact DeepFM BPR backbone candidate")
    autonomous_backbone.add_argument("--repository-root", type=Path, default=Path("."))
    autonomous_backbone.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    autonomous_backbone.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    autonomous_backbone.add_argument("--parent-ledger", type=Path, default=Path("artifacts/autonomous-ranking-verified/ledger.sqlite"))
    autonomous_backbone.add_argument("--output-dir", type=Path, default=Path("artifacts/autonomous-backbone"))
    submission = commands.add_parser("submission", help="generate a CSV from one frozen checkpoint manifest")
    submission.add_argument("--ledger", type=Path, required=True)
    submission.add_argument("--run-id", required=True)
    submission.add_argument("--starter-kit", type=Path, default=Path("kuairand-starter-kit"))
    submission.add_argument("--data-dir", type=Path, default=Path("kuairand-starter-kit/KuaiRand-Pure/data"))
    submission.add_argument("--output", type=Path, required=True)
    preflight = commands.add_parser("scale-preflight", help="stream and validate a KuaiRand-1K/27K bonus artifact")
    preflight.add_argument("--variant", choices=("1k", "27k"), required=True)
    preflight.add_argument("--data-dir", type=Path, required=True)
    preflight.add_argument("--output", type=Path, required=True)
    scale_baseline = commands.add_parser("scale-popularity", help="run streaming popularity baseline on KuaiRand-1K/27K validation")
    scale_baseline.add_argument("--variant", choices=("1k", "27k"), required=True)
    scale_baseline.add_argument("--data-dir", type=Path, required=True)
    scale_baseline.add_argument("--evaluator", type=Path, default=Path("kuairand-starter-kit/evaluate.py"))
    scale_baseline.add_argument("--hash-bits", type=int, help="fixed popularity-table bits; defaults to 24 for 27K and exact counts for 1K")
    scale_baseline.add_argument("--shards", type=int, default=256, help="number of user-consistent validation shards")
    scale_baseline.add_argument("--scratch-dir", type=Path, default=Path("artifacts/scale-scratch"), help="ignored temporary directory for sharded validation")
    args = parser.parse_args()
    if args.command == "qualification":
        print(json.dumps(run_qualification(args.output_dir), indent=2, sort_keys=True))
    elif args.command == "report":
        ledger = ExperimentLedger(args.ledger)
        try:
            print(write_report(ledger, args.output))
        finally:
            ledger.close()
    elif args.command == "campaign-status":
        print(write_campaign_report(args.campaign, args.output))
    elif args.command == "designate-final":
        print(json.dumps(designate_final(campaign_report_path=args.campaign_report, final_ledger_path=args.final_ledger), indent=2, sort_keys=True))
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
    elif args.command == "autonomous-watchtime":
        print(json.dumps(run_autonomous_watchtime(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, parent_ledger_path=args.parent_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "autonomous-negative-sampling":
        print(json.dumps(run_autonomous_negative_sampling(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, parent_ledger_path=args.parent_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "autonomous-lambda-ranking":
        print(json.dumps(run_autonomous_lambda_ranking(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, parent_ledger_path=args.parent_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "autonomous-ensemble":
        print(json.dumps(run_autonomous_ensemble(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, bpr_ledger_path=args.bpr_ledger, history_ledger_path=args.history_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "autonomous-temporal":
        print(json.dumps(run_autonomous_temporal(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, parent_ledger_path=args.parent_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "autonomous-three-ensemble":
        print(json.dumps(run_autonomous_three_ensemble(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, bpr_ledger_path=args.bpr_ledger, history_ledger_path=args.history_ledger, temporal_ledger_path=args.temporal_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "autonomous-backbone":
        print(json.dumps(run_autonomous_backbone(repository_root=args.repository_root, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, parent_ledger_path=args.parent_ledger, output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "submission":
        print(generate_submission(ledger_path=args.ledger, run_id=args.run_id, starter_kit_dir=args.starter_kit, data_dir=args.data_dir, output_path=args.output))
    elif args.command == "scale-preflight":
        print(write_preflight(ScaleArtifactAdapter(args.variant, args.data_dir), args.output))
    elif args.command == "scale-popularity":
        print(json.dumps(run_streaming_popularity(variant=args.variant, data_dir=args.data_dir, evaluator_path=args.evaluator, hash_bits=args.hash_bits, shards=args.shards, scratch_dir=args.scratch_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
