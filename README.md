# TikTok TechJam 2026 — Track 2

An autonomous ML research agent for recommender systems. It turns a benchmark contract into a controlled research loop: reproduce a baseline, propose bounded candidates, train and validate them safely, recover from failures, preserve evidence, and generate predictions from the exact frozen checkpoint that was measured.

The current KuaiRand-Pure campaign is complete under a versioned **team-interpreted** Starter Kit contract. It has a converged validation result, immutable final-record provenance, and a schema-valid feature-only output. It does **not** claim an organizer-confirmed or hidden-test score.

## What the system does

```text
Benchmark contract + evidence + frozen parent checkpoints
                         |
                         v
                 bounded candidate batch
                         |
                         v
          isolated execution and validation-only scoring
                         |
                         v
   immutable ledger + reflection + recovery + convergence check
                         |
                         v
        frozen checkpoint -> feature-only submission output
```

The implementation provides:

- a safe KuaiRand adapter that refuses test-label access and test scoring during development;
- organizer-evaluator delegation with evaluator and data identities bound to every campaign;
- isolated candidate worktrees, patch-policy checks, deadlines, recovery records, and an append-only SQLite ledger;
- pointwise FM parity, within-user BPR and listwise ranking candidates, leakage-safe history and temporal features, auxiliary-feedback candidates, and frozen rank ensembles;
- checkpoint-backed output generation: predictions are made from the scored checkpoint, never a later retrain;
- streaming 1K/27K processing with bounded counters, user-consistent validation shards, checkpoint/resume support, and byte-identical output recovery; and
- a data-free GitHub Actions integrity suite for the public repository.

## Measured results

All figures below are validation-only and use the Starter Kit profile described in the next section. They are not hidden-test or leaderboard results.

### KuaiRand-Pure

| Run | GAUC | nDCG@5 | Primary | Evidence |
|---|---:|---:|---:|---|
| Reproduced organizer NumPy FM baseline (5 seeds) | 0.667400 | 0.535744 | 0.601572 | R001 |
| PyTorch pointwise FM control (5 seeds) | 0.667450 | 0.535794 | 0.601622 | R002 |
| BPR ranking FM (5 seeds) | 0.669535 | 0.536629 | 0.603082 | R003 |
| Frozen BPR/history/temporal blend (5 seeds) | 0.670845 | 0.537188 | **0.604017** | R010/R023/R027 |

The final blend improves the reproduced baseline by **+0.002445 primary**. Its declared weights are 0.375 BPR, 0.375 history, and 0.250 temporal. The campaign revalidated that leader, then recorded three declared non-significant confirmation batches under one data fingerprint and evaluator hash (epsilon = 0.002, N = 3). It used 26.65 CPU seconds, 0 GPU seconds, 0 LLM tokens, and 0 manual interventions across those four campaign records.

The designated record `final-07eadac3e123` is bound to the frozen checkpoint SHA-256 `85bc25db…921c2f`. It generated a 170,588-row feature-only CSV with SHA-256 `60538bb…a672`; no test labels were read or scored.

### KuaiRand bonus-scale evidence

| Dataset / model | GAUC | nDCG@5 | Primary | Scope |
|---|---:|---:|---:|---|
| 1K item-only streaming baseline | 0.542570 | 0.545226 | 0.543898 | validation |
| 1K item × tab blend | 0.542923 | 0.548764 | 0.545843 | validation |
| 27K bounded item-only baseline | 0.570914 | 0.544153 | 0.557534 | validation |
| 27K item × tab blend | 0.574100 | 0.599412 | **0.586756** | validation |

The 27K output path streamed all 114,832,239 test feature rows from its frozen model and proved that an interrupted run resumes to the byte-identical output (SHA-256 `c4e95a…fcc5`). These scale figures demonstrate robustness and bounded processing, not an official bonus-benchmark threshold: no organizer reference threshold has been supplied.

See [results_log.md](results_log.md) for every measured result, including regressions, recovery events, hashes, commands, and limitations.

## Benchmark contract and integrity

The official PDF is internally inconsistent: its narrative pages describe `click`, NDCG@10, and Recall@50, while the detailed Starter Kit section provides runnable code for `long_view`, GAUC, nDCG@5, epsilon = 0.002, N = 3, and the output schema below.

**Interpretation — not explicit organizer wording:** this project uses the versioned Starter Kit as the executable internal contract. If organizers issue a corrected evaluator, it receives a new identity and affected results must be rerun. The project therefore labels its final record `team_interpreted`, rather than organizer-confirmed. Full rationale: [docs/PROBLEM.md](docs/PROBLEM.md), [docs/DECISIONS.md](docs/DECISIONS.md), and [docs/DELIVERY_AUDIT.md](docs/DELIVERY_AUDIT.md).

Development safeguards include:

- test labels are structurally unavailable to candidate-facing code;
- metric calculation is delegated to the organizer evaluator, whose SHA-256 is recorded;
- candidate results bind code, configuration, data, evaluator, prediction, and checkpoint identities;
- campaigns reject mixed evaluator/data identities and single-seed selection;
- submission generation accepts feature-only test rows and never retrains or scores them; and
- all research outcomes—including failures and regressions—remain in the append-only evidence record.

## Repository map

- `src/tiktok_ml_agent/` — benchmark contracts, safe adapters, controller, models, recovery, reporting, and submission generation
- `tests/` — deterministic integrity, model, isolation, recovery, scale, and repository-safety tests
- `experiments/` — declared campaign configuration
- `scripts/` — checksum-verified KuaiRand downloader
- `docs/` — problem statement, requirements, architecture, decisions, experiment registry, demo script, provenance, and delivery audit
- `results_log.md` — complete empirical record
- `changelog.md` — newest-first implementation and release handoff log
- `artifacts/` — local-only checkpoints, ledgers, outputs, and reports (ignored by Git)

## Setup

Requirements: Python 3.11+ and [uv](https://docs.astral.sh/uv/).

Obtain the organizer Starter Kit separately from the competition materials. Place its unmodified source files (including `evaluate.py`) in `kuairand-starter-kit/`. The directory is intentionally ignored, along with datasets and generated artifacts; do not force-add any of them.

```bash
uv sync
source .venv/bin/activate

# Downloads the declared dataset archive, not Starter Kit source.
python scripts/download_kuairand.py pure
```

For optional scale artifacts, use `python scripts/download_kuairand.py 1k` or `27k`.

## Reproduce safely

Run the public, data-free checks:

```bash
uv run python -m unittest discover -s tests -v
git diff --check
```

With the separately obtained Starter Kit and KuaiRand-Pure data installed, reproduce the core workflow:

```bash
.venv/bin/python -m tiktok_ml_agent qualification
.venv/bin/python -m tiktok_ml_agent baseline-valid
.venv/bin/python -m tiktok_ml_agent autonomous-ranking
.venv/bin/python -m tiktok_ml_agent campaign-status \
  --campaign experiments/kuairand-pure-team-interpreted-campaign.json \
  --output artifacts/campaigns/kuairand-pure-team-interpreted-v1.json
.venv/bin/python -m tiktok_ml_agent designate-final \
  --campaign-report artifacts/campaigns/kuairand-pure-team-interpreted-v1.json \
  --final-ledger artifacts/finals/kuairand-pure-team-interpreted.sqlite
.venv/bin/python -m tiktok_ml_agent submission \
  --ledger artifacts/finals/kuairand-pure-team-interpreted.sqlite \
  --run-id final-07eadac3e123 \
  --output artifacts/submissions/kuairand-pure-team-interpreted-final.csv
```

`submission` validates the required provisional schema:

```text
row_id,user_id,video_id,score
```

It generates aligned finite scores from the frozen checkpoint and does not score local test labels.

## Limitations and delivery status

- The organizer must resolve the PDF/Starter Kit metric conflict before any organizer-confirmed claim.
- The reported campaign used the deterministic offline planner. The optional Responses-API planner is schema-bounded and tested, but was not used in the measured campaign; reported LLM usage is therefore genuinely zero.
- The repository excludes organizer source/data because the data is CC BY-SA 4.0 and the separately supplied Starter Kit source has no separate license notice.
- The public code repository and CI are ready. Remaining external delivery actions are a public three-minute YouTube demo and official Devpost/submission steps.

For the full delivery checklist, see [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md). For contribution and review expectations, see [docs/COLLABORATION.md](docs/COLLABORATION.md).
