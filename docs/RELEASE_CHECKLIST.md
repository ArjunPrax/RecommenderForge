# Release Checklist

Status: Human-gated external actions are intentionally unchecked. This checklist does not grant permission to publish, submit, or change repository visibility.

## Technical evidence

- [ ] Organizer clarification for REQ-014 recorded, or final report clearly retains the provisional contract.
- [ ] KuaiRand-Pure campaign converged through `campaign-status` with a single evaluator identity.
- [ ] `designate-final` created the immutable final record from that campaign.
- [ ] `submission` generated the final Starter Kit schema output from the designated record.
- [ ] KuaiRand-1K and KuaiRand-27K artifact status/results are recorded honestly.
- [ ] Full test suite and `git diff --check` pass at the release commit.
- [ ] Resource report states LLM input/output tokens and GPU-hours to convergence.

## Documentation

- [ ] README contains overview, setup, reproduction, limitations, and contributions.
- [ ] `results_log.md` includes successes, regressions, failures/recovery, and final delta table.
- [ ] Devpost draft is updated with final measured evidence and submitted by a human.

## Human-authorized external actions

- [ ] Verify organizer Starter Kit redistribution terms before publishing it.
- [ ] Scan tracked files for credentials/private data.
- [ ] Make the GitHub repository public only after human review.
- [ ] Push the reviewed release branch and merge through a PR.
- [ ] Submit the output/checkpoint through the official competition flow.
