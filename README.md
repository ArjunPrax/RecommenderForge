# TikTok TechJam 2026 - Track 2

Autonomous ML research agent for TikTok TechJam 2026 Track 2. The project is in implementation Phase 1.

The project will address the official Track 2 challenge: an autonomous ML research agent for recommender systems. Exact organizer wording, requirements, and unresolved source conflicts are in [docs/PROBLEM.md](docs/PROBLEM.md) and [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md).

Official KuaiRand variants can be downloaded with checksum verification, for example: `python scripts/download_kuairand.py 1k`. Data stays untracked.

For the large official artifact, the scale baseline is deliberately bounded-memory: `python -m tiktok_ml_agent scale-popularity --variant 27k --data-dir kuairand-starter-kit/KuaiRand-27K/data`. It keeps test labels unavailable and evaluates validation in user-consistent shards.

## Start here

Read [AGENTS.md](AGENTS.md), then the context listed there. The repository is the durable project memory.

## Repository map

- `docs/` - problem, requirements, decisions, plan, collaboration, experiments, demo, references
- `src/tiktok_ml_agent/` - benchmark contracts, safe adapters, research controller, model candidates, reporting, submission
- `tests/` - deterministic integrity, metric, isolation, model, and recovery tests
- `scripts/` - checksum-verified official KuaiRand downloader
- `artifacts/` - ignored ledgers, checkpoints, reports, outputs, and scale preflights
- `changelog.md` - newest-first handoff log
- `results_log.md` - reproducible measured outcomes
- `.github/` - lightweight PR and issue templates

## Current implementation target

The agent reproduces the organizer KuaiRand-Pure baseline, proposes bounded research candidates, executes each candidate in an isolated worktree, evaluates only permitted validation data, recovers from failures, records complete evidence, and freezes the exact validation-best checkpoint for submission.

The official PDF currently conflicts over the target/metrics. The supplied starter-kit evaluator is the provisional executable contract; see [docs/PROBLEM.md](docs/PROBLEM.md) and [docs/DECISIONS.md](docs/DECISIONS.md).

## Safe reproduction commands

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m tiktok_ml_agent qualification
.venv/bin/python -m tiktok_ml_agent baseline-valid
.venv/bin/python -m tiktok_ml_agent autonomous-ranking
.venv/bin/python -m tiktok_ml_agent campaign-status --campaign path/to/campaign.json --output artifacts/campaign.json
```

All development commands are validation-only. `submission` reconstructs a measured frozen checkpoint and validates row alignment; it does not score local test labels.

## Start here

Read [AGENTS.md](AGENTS.md), [docs/PLAN.md](docs/PLAN.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/HANDOFF.md](docs/HANDOFF.md). Do not download or commit competition data until the ignore rules and benchmark contract are reviewed.
