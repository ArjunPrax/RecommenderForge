# Release Checklist

Status: Human-gated external actions are intentionally unchecked. This checklist does not grant permission to publish, submit, or change repository visibility.

## Technical evidence

- [x] Final campaign report clearly retains the provisional contract and blocks finalization until REQ-014 is resolved.
- [x] KuaiRand-Pure provisional campaign converged through `campaign-status` with a single evaluator and data identity.
- [ ] `designate-final` created the immutable final record from that campaign.
- [ ] `submission` generated the final Starter Kit schema output from the designated record.
- [x] KuaiRand-1K and KuaiRand-27K artifact status/results are recorded honestly.
- [x] Full test suite and `git diff --check` pass at the current release-candidate commit.
- [x] Provisional campaign report states LLM input/output tokens and GPU-hours to convergence.

## Documentation

- [x] README contains overview, setup, reproduction, limitations, and contribution/provenance context.
- [x] `results_log.md` includes successes, regressions, failures/recovery, and the provisional campaign delta table.
- [ ] Devpost draft is updated with final measured evidence and submitted by a human.

## Human-authorized external actions

- [ ] Verify organizer Starter Kit redistribution terms before publishing it.
- [ ] Scan tracked files for credentials/private data.
- [ ] Make the GitHub repository public only after human review.
- [ ] Push the reviewed release branch and merge through a PR.
- [ ] Submit the output/checkpoint through the official competition flow.
