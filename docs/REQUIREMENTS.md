# Track 2 Requirements

Source: updated official PDF pages 3-12 and the organizer Starter Kit. Conflicting source statements are retained rather than silently reconciled.

| ID | Source | Requirement | Mandatory / Optional | How we will eventually prove compliance | Status |
|---|---|---|---|---|---|
| REQ-001 | p. 3 | Design and implement an autonomous ML research agent for recommender systems. | Mandatory | End-to-end run, code, logs, submission. | Partially demonstrated: qualification and bounded validation-only research loops; final convergence/submission pending |
| REQ-002 | p. 3 | Reproduce organizer official baseline and confirm reported validation score. | Mandatory | Reproducible baseline run and metrics. | Reproduced on validation; see R001 |
| REQ-003 | p. 3 | Iterate using training split and public validation feedback only; never access hidden test during development. | Mandatory | Data-access controls and run logs. | Partially demonstrated: fail-closed access controls and validation-only research runs are unit-tested; final campaign audit pending |
| REQ-004 | p. 3 | Repeatedly improve relative to official baseline; final hidden-test score uses final designated submission. | Mandatory target | Iteration logs and organizer evaluation. | Partially demonstrated on validation: R008 is +0.002193; final hidden-test claim pending |
| REQ-005 | p. 3 | Improve autonomously across full stack with minimal human intervention. | Mandatory | Intervention summary and logs. | Partially demonstrated: recorded runs had zero mid-run interventions; final convergence pending |
| REQ-006 | p. 3, 9 | Recover/retry/route around errors, timeouts, unexpected inputs; long runs must not crash, stall, or diverge. | Mandatory | Recovery evidence in run logs. | Partially demonstrated: R005 is a ledgered recovered execution; timeout/memory routes not yet demonstrated |
| REQ-007 | pp. 4, 6 | Do not use external training data or weights trained on test labels. | Mandatory | Data/model provenance record. | Not evaluated |
| REQ-008 | p. 4 | Use fixed organizer splits and metrics. Compute budget is TBD. | Mandatory | Evaluation configuration. | Partially demonstrated: all current results bind the provisional organizer evaluator hash; REQ-014 still blocks final metric designation |
| REQ-009 | p. 5 | Log each iteration's hypothesis, code diff, metrics, and errors/recovery events. | Mandatory | Complete per-iteration log. | Partially demonstrated for R005/R006 and autonomous objective runs |
| REQ-010 | p. 7 | Submit Devpost description including tools, APIs, libraries, datasets/assets. | Mandatory | Submitted Devpost content. | Drafted locally in `docs/DEVPOST_DRAFT.md`; human submission and final-evidence update pending |
| REQ-011 | p. 7 | Submit a public repository and README with overview, setup, reproduction, limitations, contributions. | Mandatory | Public final repository and README. | README/release checklist prepared; human authorization for visibility/publication pending |
| REQ-012 | pp. 7-8 | Submit final output/checkpoint in Starter Kit schema and validation-best results/delta table. | Mandatory | Validated output and results table. | Partially demonstrated: checkpoint-backed, schema-valid EXP-005 output generated; no final designated submission |
| REQ-013 | p. 8 | Report total LLM input/output tokens and GPU-hours to convergence. | Mandatory | Resource-use records. | Partially demonstrated: immutable run records plus explicit campaign aggregation implemented; final converged campaign pending |
| REQ-014 | pp. 4-8 | PDF conflicts: Starter Kit uses `long_view` / GAUC / nDCG@5; narrative uses `click` / nDCG@10 / Recall@50. | Clarification required | Organizer response and versioned benchmark contract. | Blocked |
| REQ-015 | p. 5 | Provisional Starter Kit submission schema is `row_id,user_id,video_id,score`; rows must validate for alignment and finite scores. | Conditional | Adapter validation against organizer check semantics. | Partially demonstrated: checkpoint-backed outputs validate alignment and finite scores; final designated output pending |
| REQ-016 | p. 5 | Provisional Starter Kit convergence uses epsilon=0.002 and N=3. | Conditional | Versioned iteration history. | Partially demonstrated: batch-level campaign evaluator and tests implemented; final campaign pending |
| REQ-017 | p. 5 | Development must not use hidden test despite locally available labels. | Mandatory | Fail-closed adapter, audit events, and tests. | Implemented and unit-tested; final-run audit pending |
| REQ-018 | pp. 5, 8 | Final output must be generated from the validation-best checkpoint at convergence. | Mandatory | Checkpoint manifest and reproducible predictions. | Partially demonstrated: EXP-005 output loads its frozen validation-best seed; final convergence pending |
| REQ-019 | pp. 5, 7, 9 | Agent must retain per-iteration reasoning and resource/intervention evidence. | Mandatory | Append-only run ledger and generated report. | Partially demonstrated: qualification and real research ledgers/reports exist; final campaign evidence pending |

The PDF permits open-source libraries/frameworks, papers, public solutions, and pretrained weights except as limited by REQ-007. It mandates no technical stack.
