# Collaboration

`main` is the integrated working state. Avoid direct feature development on it. The existing `Arjun` branch prevents Git from creating `arjun/...` branches, so use `arjun-T2-XXX-short-name`; use `divija-T2-XXX-short-name` for the other contributor namespace.

Normal flow: task -> branch -> implementation -> local validation -> documentation/log updates -> push -> PR -> review -> merge. PRs should state what changed, why, testing, requirement/task, experiment/result, and known limitations. Each human should review the other's meaningful PRs where practical.

The branch owner remains responsible for correctness, understanding, testing, security, performance claims, and PR quality. Agree ownership before overlapping work, communicate interface changes early, and avoid concurrent edits to central files where practical. Keep process lightweight.

## Ownership

The platform scope covers benchmark adapters, integrity controls, controller/ledger/memory/recovery, integration, and reporting. The modeling scope covers model plugins, PyTorch parity, ranking/history/multi-task experiments, and scale adaptations. Cross-review is useful, but automated invariants and human approval are the integrity controls.

## Required PR evidence

State task ID, requirement IDs, experiment ID/run class, parent checkpoint/commit, operator family, validation commands, measured result or **Not yet demonstrated**, documentation changes, and known limitations.
