# Demo

Status: Demo-ready provisionally. The final event includes Presentation & Communication scoring.

## Officially captured evidence

- Devpost project description.
- Public repository with code and README.
- Per-iteration logs and manual-intervention summary.
- Final submission/checkpoint, results table, LLM-token total, and GPU-hours.

## Demo objective

Show a complete autonomous qualification/research run: benchmark contract, runtime hypothesis selection, isolated candidate execution, recovery event, evidence ledger, convergence, and exact checkpoint-backed output.

## Three-minute flow

1. State the benchmark and no-hidden-test policy.
2. Show the planner's retrieved evidence and candidate batch.
3. Show one candidate result and the mechanism-aware reflection.
4. Show a recovery record and intervention count.
5. Show the frozen checkpoint manifest, report, and valid output.

## Normal case

The agent reaches a converged result without manual mid-run code changes and produces an evidence report.

## Failure/degraded/edge case

Use recorded qualification artifacts and deterministic fixtures if live data/training is unavailable.

## What judges should observe

The agent's research reasoning is traceable, its test access is blocked, and the submitted artifact is the measured model.

## Commands

`python -m tiktok_ml_agent qualification --output-dir artifacts/qualification`

For the first real, validation-only objective batch:

`python -m tiktok_ml_agent autonomous-ranking --output-dir artifacts/autonomous-ranking`

The second command deliberately does not accept a test-score option.

The checkpoint-parented history-cross continuation is:

`python -m tiktok_ml_agent autonomous-history --parent-ledger artifacts/autonomous-ranking-verified/ledger.sqlite --output-dir artifacts/autonomous-history`

## Demonstrated output

The qualification workflow records a controlled failure and enforced deadline recovery. The Pure campaign records a revalidated leader, three post-leader confirmations, data/evaluator identities, resource totals, a team-interpreted designated-final record, and a feature-only output from the frozen leader. The demo must not call this an organizer-confirmed or hidden-test submission.

## Recovery plan

Stop the affected candidate, preserve artifacts, resume from the immutable parent, and show the ledger recovery event.

## Backup demo

Use a pre-generated report, ledger export, and checkpoint manifest.

## Architecture visual

Controller -> isolated candidates -> evaluator -> ledger/memory -> reflection/convergence -> checkpoint-backed output.
