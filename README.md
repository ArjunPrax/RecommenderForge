# TikTok TechJam 2026 - Track 2

Autonomous ML research agent for TikTok TechJam 2026 Track 2. The project has a measured, converged **team-interpreted** KuaiRand-Pure campaign, an immutable designated-final record, and a schema-valid feature-only output. It does not claim organizer confirmation or a hidden-test result.

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

The official PDF conflicts over the target/metrics. **Interpretation - not explicit organizer wording:** D029 uses the detailed Starter Kit as the pinned execution contract (`long_view`, GAUC, nDCG@5); D031 distinguishes this team interpretation from organizer confirmation. Any corrected evaluator is a new incompatible profile that must be rerun. See [docs/PROBLEM.md](docs/PROBLEM.md) and [docs/DECISIONS.md](docs/DECISIONS.md).

The revalidated provisional campaign leader has validation primary `0.604017` against reproduced baseline `0.601572` (+`0.002445`). This is not a hidden-test or official leaderboard claim; complete evidence is in [results_log.md](results_log.md#r023---revalidated-converged-provisional-pure-campaign).

## Safe reproduction commands

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m tiktok_ml_agent qualification
.venv/bin/python -m tiktok_ml_agent baseline-valid
.venv/bin/python -m tiktok_ml_agent autonomous-ranking
.venv/bin/python -m tiktok_ml_agent campaign-status --campaign experiments/kuairand-pure-team-interpreted-campaign.json --output artifacts/campaigns/kuairand-pure-team-interpreted-v1.json
.venv/bin/python -m tiktok_ml_agent designate-final --campaign-report artifacts/campaigns/kuairand-pure-team-interpreted-v1.json --final-ledger artifacts/finals/kuairand-pure-team-interpreted.sqlite
.venv/bin/python -m tiktok_ml_agent submission --ledger artifacts/finals/kuairand-pure-team-interpreted.sqlite --run-id final-07eadac3e123 --output artifacts/submissions/kuairand-pure-team-interpreted-final.csv
```

All development commands are validation-only. `submission` reconstructs a measured frozen checkpoint and validates row alignment; it does not score local test labels. `designate-final` rejects a `provisional` campaign, and records `team_interpreted` separately from organizer-`confirmed` designation.

## Contributions

The team designed the benchmark contract and delivery direction. Codex implemented and verified the safety controls, autonomous research workflow, model experiments, large-scale recovery, immutable artifact chain, and documentation. The repository history preserves the contribution-level evidence for review.

## Start here

Read [AGENTS.md](AGENTS.md), [docs/PLAN.md](docs/PLAN.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md), and [changelog.md](changelog.md). Do not commit competition data.
