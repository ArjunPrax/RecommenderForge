# Release Checklist

Status: Human-gated external actions are intentionally unchecked. This checklist does not grant permission to publish, submit, or change repository visibility.

## Technical evidence

- [x] Campaign report explicitly distinguishes `team_interpreted` from organizer-confirmed designation.
- [x] KuaiRand-Pure team-interpreted campaign converged through `campaign-status` with a single evaluator and data identity.
- [x] `designate-final` created the immutable team-interpreted final record from that campaign.
- [x] `submission` generated the aligned Starter Kit schema output from the designated record.
- [x] KuaiRand-1K and KuaiRand-27K artifact status/results are recorded honestly.
- [x] R028 proves a deadline kills a real trusted child and removes its disposable worktree.
- [x] Full test suite (70 tests) and `git diff --check` pass at the current release-candidate commit.
- [x] Team-interpreted campaign report states LLM input/output tokens and GPU-hours to convergence.

## Documentation

- [x] README contains overview, setup, reproduction, limitations, and contribution/provenance context.
- [x] `results_log.md` includes successes, regressions, failures/recovery, campaign delta table, and team-interpreted designation evidence.
- [x] Devpost draft is updated with current measured evidence; human submission remains pending.

## Human-authorized external actions

- [ ] Verify organizer Starter Kit redistribution terms before publishing it (the whole local kit is ignored until then).
- [x] Scan tracked files for credential signatures/private-key markers; none were found. Competition data remains ignored.
- [ ] Make the GitHub repository public only after human review.
- [ ] Push the reviewed release branch and merge through a PR.
- [ ] Submit the output/checkpoint through the official competition flow.
