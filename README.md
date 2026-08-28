# TikTok TechJam 2026 - Track 2

Autonomous ML research agent for TikTok TechJam 2026 Track 2. The project has a measured, converged **provisional** KuaiRand-Pure campaign; organizer metric clarification and human release actions remain outstanding.

The project will address the official Track 2 challenge: an autonomous ML research agent for recommender systems. Exact organizer wording, requirements, and unresolved source conflicts are in [docs/PROBLEM.md](docs/PROBLEM.md) and [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md).

Official KuaiRand variants can be downloaded with checksum verification, for example: `python scripts/download_kuairand.py 1k`. Data stays untracked.

For the large official artifact, the scale baseline is deliberately bounded-memory: `python -m tiktok_ml_agent scale-popularity --variant 27k --data-dir kuairand-starter-kit/KuaiRand-27K/data --output artifacts/scale/kuairand-27k-baseline.json`. It keeps test labels unavailable and evaluates validation in user-consistent shards; `--output` preserves the measured JSON artifact.

## Repository map

- `docs/` - problem, requirements, decisions, plan, collaboration, experiments, demo, provenance, and organizer clarification draft
- `src/tiktok_ml_agent/` - benchmark contracts, safe adapters, research controller, model candidates, reporting, submission
- `tests/` - deterministic integrity, metric, isolation, model, and recovery tests
- `scripts/` - checksum-verified official KuaiRand downloader
- `artifacts/` - ignored ledgers, checkpoints, reports, outputs, and scale preflights
- `changelog.md` - newest-first handoff log
- `results_log.md` - reproducible measured outcomes
- `.github/` - lightweight PR and issue templates

## Current implementation target

The agent reproduces the organizer KuaiRand-Pure baseline, proposes bounded research candidates, executes each candidate in an isolated worktree, evaluates only permitted validation data, recovers from failures, records complete evidence, and freezes the exact validation-best checkpoint for output generation. It also enforces candidate deadlines, common evaluator/data identities in campaigns, and atomic output publication.

The official PDF currently conflicts over the target/metrics. The supplied starter-kit evaluator is the provisional executable contract; see [docs/PROBLEM.md](docs/PROBLEM.md), [docs/DECISIONS.md](docs/DECISIONS.md), and the ready-to-send [organizer questions](docs/ORGANIZER_CLARIFICATION_EMAIL.md).

The revalidated provisional campaign leader has validation primary `0.604017` against reproduced baseline `0.601572` (+`0.002445`). This is not a hidden-test or official leaderboard claim; complete evidence is in [results_log.md](results_log.md#r023---revalidated-converged-provisional-pure-campaign).

## Safe reproduction commands

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m tiktok_ml_agent qualification
.venv/bin/python -m tiktok_ml_agent baseline-valid
.venv/bin/python -m tiktok_ml_agent autonomous-ranking
.venv/bin/python -m tiktok_ml_agent campaign-status --campaign experiments/kuairand-pure-provisional-campaign.json --output artifacts/campaigns/kuairand-pure-provisional-v1.json
.venv/bin/python -m tiktok_ml_agent submission --ledger artifacts/autonomous-ensemble-revalidation/ledger.sqlite --run-id exp-009e-367544f3516d --output artifacts/submissions/kuairand-pure-provisional-campaign-leader.csv
```

All development commands are validation-only. `submission` reconstructs a measured frozen checkpoint and validates row alignment; it does not score local test labels. `designate-final` intentionally rejects the included campaign until the organizer contract is confirmed.

## Start here

Read [AGENTS.md](AGENTS.md), [docs/PLAN.md](docs/PLAN.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), and [changelog.md](changelog.md). Do not commit competition data.
