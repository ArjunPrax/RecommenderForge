# Claude Collaboration Instructions

Read `AGENTS.md`, `docs/PLAN.md`, `docs/ARCHITECTURE.md`, `docs/EXPERIMENTS.md`, the current handoffs, and `changelog.md` before starting a task.

## Scope and ownership

Claude owns model plugins, NumPy/PyTorch parity, ranking/history/multi-feedback experiments, and scale adaptations. Do not edit controller, benchmark integrity, ledger, memory, recovery, or integration files without an interface-approved task.

## Non-negotiable safeguards

- Never access or score hidden-test labels.
- Use the organizer evaluator through the adapter; do not reimplement it.
- Never select a final winner from one seed.
- Preserve the exact checkpoint whose validation score is reported.
- Keep every experiment in an isolated task branch/worktree and record failures as well as successes.
- Mark statements without measured evidence as **Not yet demonstrated**.

## PR and handoff protocol

Use `divija-T2-XXX-short-name`. State task/requirement/experiment IDs, operator family, parent checkpoint, tests, measured results, and limitations. Update `docs/handoffs/claude.md` and the PR; do not overwrite Codex-owned handoffs.
