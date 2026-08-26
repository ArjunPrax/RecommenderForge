# Track 2 Requirements

Source: official PDF pages 3-9. All statuses are intentionally not evaluated during Phase 0. Conflicting source statements are retained rather than reconciled.

| ID | Source | Requirement | Mandatory / Optional | How we will eventually prove compliance | Status |
|---|---|---|---|---|---|
| REQ-001 | p. 3 | Design and implement an autonomous ML research agent for recommender systems. | Mandatory | End-to-end run, code, logs, submission. | Not started |
| REQ-002 | p. 3 | Reproduce organizer official baseline and confirm reported validation score. | Mandatory | Reproducible baseline run and metrics. | Not evaluated |
| REQ-003 | p. 3 | Iterate using training split and public validation feedback only; never access hidden test during development. | Mandatory | Data-access controls and run logs. | Not evaluated |
| REQ-004 | p. 3 | Repeatedly improve relative to official baseline; final hidden-test score uses final designated submission. | Mandatory target | Iteration logs and organizer evaluation. | Not evaluated |
| REQ-005 | p. 3 | Improve autonomously across full stack with minimal human intervention. | Mandatory | Intervention summary and logs. | Not evaluated |
| REQ-006 | p. 3, 9 | Recover/retry/route around errors, timeouts, unexpected inputs; long runs must not crash, stall, or diverge. | Mandatory | Recovery evidence in run logs. | Not evaluated |
| REQ-007 | pp. 4, 6 | Do not use external training data or weights trained on test labels. | Mandatory | Data/model provenance record. | Not evaluated |
| REQ-008 | p. 4 | Use fixed organizer splits and metrics. Compute budget is TBD. | Mandatory | Evaluation configuration. | Not evaluated |
| REQ-009 | p. 5 | Log each iteration's hypothesis, code diff, metrics, and errors/recovery events. | Mandatory | Complete per-iteration log. | Not started |
| REQ-010 | p. 7 | Submit Devpost description including tools, APIs, libraries, datasets/assets. | Mandatory | Submitted Devpost content. | Not started |
| REQ-011 | p. 7 | Submit a public repository and README with overview, setup, reproduction, limitations, contributions. | Mandatory | Public final repository and README. | Not started |
| REQ-012 | pp. 7-8 | Submit final output/checkpoint in Starter Kit schema and validation-best results/delta table. | Mandatory | Validated output and results table. | Not started |
| REQ-013 | p. 8 | Report total LLM input/output tokens and GPU-hours to convergence. | Mandatory | Resource-use records. | Not started |
| REQ-014 | pp. 3-8 | PDF conflicts: AliCCP is required in pp. 3/7/8; KuaiRand-Pure is required in pp. 5-6. | Clarification required | Organizer clarification and decision record. | Blocked |
| REQ-015 | p. 5 | If KuaiRand Starter Kit governs: CSV header `row_id,user_id,video_id,score`; generate `python3 submit.py --make`, validate with `--check`. | Conditional | Official Starter Kit validation. | Not evaluated |
| REQ-016 | p. 5 | If KuaiRand Starter Kit governs: convergence epsilon=0.002, N=3. | Conditional | Official iteration history. | Not evaluated |

The PDF permits open-source libraries/frameworks, papers, public solutions, and pretrained weights except as limited by REQ-007. It mandates no technical stack.
