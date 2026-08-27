# TikTok TechJam 2026 - Track 2

Autonomous ML research agent for TikTok TechJam 2026 Track 2. The project is in implementation Phase 1.

The project will address the official Track 2 challenge: an autonomous ML research agent for recommender systems. Exact organizer wording, requirements, and unresolved source conflicts are in [docs/PROBLEM.md](docs/PROBLEM.md) and [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md).

Official KuaiRand variants can be downloaded with checksum verification, for example: `python scripts/download_kuairand.py 1k`. Data stays untracked.

## Start here

Read [AGENTS.md](AGENTS.md), then the context listed there. The repository is the durable project memory.

## Repository map

- `docs/` - problem, requirements, decisions, plan, collaboration, experiments, demo, references
- `src/`, `tests/`, `experiments/`, `scripts/`, `artifacts/` - intentionally empty placeholders
- `changelog.md` - newest-first handoff log
- `results_log.md` - reproducible measured outcomes
- `.github/` - lightweight PR and issue templates

## Current implementation target

The agent reproduces the organizer KuaiRand-Pure baseline, proposes bounded research candidates, executes each candidate in an isolated worktree, evaluates only permitted validation data, recovers from failures, records complete evidence, and freezes the exact validation-best checkpoint for submission.

The official PDF currently conflicts over the target/metrics. The supplied starter-kit evaluator is the provisional executable contract; see [docs/PROBLEM.md](docs/PROBLEM.md) and [docs/DECISIONS.md](docs/DECISIONS.md).

## Start here

Read [AGENTS.md](AGENTS.md), [docs/PLAN.md](docs/PLAN.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/HANDOFF.md](docs/HANDOFF.md). Do not download or commit competition data until the ignore rules and benchmark contract are reviewed.
