# Results log

This is the permanent empirical record. Preserve negative results and never record hypotheses as measured outcomes.

## R026 - Strict-prior user×author affinity BPR result

Date: 2026-08-29
Experiment: EXP-018
Implementation / commit: `97caf25`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Question

Can a user's training-only long-view history with each candidate's author provide a personalised, candidate-varying signal that improves BPR ranking without reading validation or test outcomes?

### Baseline

R003 / EXP-004A five-seed BPR mean primary `0.603082`. The current frozen BPR/history/temporal ensemble leader is R010/R023 at `0.604017`.

### Change tested

Added one categorical `(user_id, author_id)` bucket to BPR FM. Each training impression receives the bucket from strictly earlier training events before its own long-view label updates state. Validation and feature-only submission rows receive the completed training state only. The candidate was run as one autonomous five-seed batch from the immutable EXP-004A parent.

### Metrics

| Metric | EXP-018 mean | Population std | Delta vs BPR |
|---|---:|---:|---:|
| GAUC | 0.669929 | 0.000374 | +0.000394 |
| nDCG@5 | 0.537001 | 0.000146 | +0.000372 |
| primary | 0.603465 | 0.000226 | +0.000383 |

The run took `115.54` CPU seconds, used zero GPU seconds and zero LLM tokens, and recorded zero manual interventions. Best seed 2 reached primary `0.603696` and is the frozen checkpoint artifact only; selection remains based on the five-seed mean.

### Correctness validation

The strict-prior/frozen-evaluation unit test passed. The runtime ordering audit found `31,951` changed within-user pairwise relations across `8,030` of `18,460` eligible validation users, proving that the feature is not user-constant or inert. The frozen best checkpoint generated `170,588` feature-only test rows plus header at `artifacts/submissions/exp-018-user-author-provisional.csv` (SHA-256 `1f2205d127a4e56c045275cb36c88e9aa79a3bc5e0b5b5526dab4e86009edfde`) without test scoring or test-label access.

### Interpretation

The personalised author-affinity mechanism is valid and improves BPR on both metric components, but its mean does not beat the current frozen three-component leader. Keep it as a provenance-complete component candidate; do not promote it over R023 or run an undisclosed ensemble search. Any ensemble evaluation must declare its vectors in advance and begin a new campaign rather than extending the converged R023 campaign.

### Limitations

This is validation-only evidence under the Starter-Kit-pinned execution contract. It is not a hidden-test score or an official organizer result. Author sparsity may send many candidates to the zero-history bucket; this candidate does not establish an improvement for every user segment.

### Reproduction

`.venv/bin/python -m tiktok_ml_agent autonomous-user-author-history --repository-root . --starter-kit kuairand-starter-kit --data-dir kuairand-starter-kit/KuaiRand-Pure/data --parent-ledger artifacts/autonomous-ranking-verified/ledger.sqlite --output-dir artifacts/autonomous-user-author-history`

## R023 - Revalidated, converged provisional Pure campaign

Date: 2026-08-28
Experiments: EXP-009E, EXP-009F, EXP-009G, EXP-009H
Implementation / commits: `81b6bf8`, with campaign safeguards from `e5307f2`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Purpose

Materialize a declared post-leader convergence campaign without silently mixing data/evaluator identities or treating a provisional organizer contract as an official final.

### Provenance repair

The first EXP-009A/EXP-009B–D draft was rejected after the campaign evaluator detected differing run-level data fingerprints. This is retained as an integrity finding, not a valid convergence claim. EXP-009E then remeasured EXP-009A's exact frozen BPR/history/temporal vector (`0.375/0.375/0.25`) after verifying every component checkpoint hash. EXP-009F–H are one-vector, frozen-component confirmations from EXP-009E; no component was retrained and no weight grid was searched.

### Campaign result

All four valid campaign records bind evaluator SHA-256 `ecfde28392eb14fec4f488083251df50624e1af2b86278b962daecfb42d195de` and data fingerprint `37d896c3e8c698f173e985917fbc714bbc8d0c93f7bf0fd2d81fbd00e7342fc4`.

| Batch | Run | Vector (BPR/history/temporal) | primary |
|---|---|---|---:|
| Leader revalidation | EXP-009E | 0.375 / 0.375 / 0.250 | 0.604017 |
| Confirmation 1 | EXP-009F | 0.500 / 0.375 / 0.125 | 0.603893 |
| Confirmation 2 | EXP-009G | 0.250 / 0.625 / 0.125 | 0.603799 |
| Confirmation 3 | EXP-009H | 0.250 / 0.250 / 0.500 | 0.603868 |

Relative to the recorded NumPy FM baseline `0.601572`, the revalidated leader is `+0.002445` primary. It becomes the significant anchor; the three later declared batches do not exceed it by ε=`0.002`, yielding stagnation `3` and provisional convergence under the starter profile.

### Resource and integrity evidence

The four campaign records aggregate `26.65` CPU seconds, `0` GPU seconds, `0` LLM input/output tokens, and `0` manual interventions. They score only validation labels. The frozen EXP-009E manifest generated `artifacts/submissions/kuairand-pure-provisional-campaign-leader.csv`: `170,588` feature-only test rows plus header, SHA-256 `60538bb59c96547bfb3e8f90ff56d8c0b5b2e2002c38ba708ecf5e2dfe82a672`.

After D027, the same frozen manifest regenerated that output through the atomic `.partial` publication path; the partial file was absent after completion and the output SHA-256 was unchanged.

### Limitation and decision

This is a **provisional** campaign, not an official final: the PDF/Starter Kit target-and-metric conflict remains REQ-014. The campaign report sets `finalization_eligible=false`; a direct `designate-final` attempt was rejected before a final record could be created. Do not submit or describe this as beating an organizer benchmark until the organizer confirms the contract.

### Reproduction

`.venv/bin/python -m tiktok_ml_agent campaign-status --campaign experiments/kuairand-pure-provisional-campaign.json --output artifacts/campaigns/kuairand-pure-provisional-v1.json`

## R022 - Strict-prior video×tab candidate-history cross regression

Date: 2026-08-28
Experiment: EXP-016
Implementation / commit: `7c2bdf8`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Question

Does a global video×tab engagement bucket, constructed strictly before each train event and frozen after training, improve BPR validation ranking?

### Baseline

R003 / EXP-004A five-seed BPR mean primary `0.603082`.

### Change Tested

Added one categorical FM field keyed by `(video_id, tab)`. Each train row receives the bucket from earlier timestamp-ordered permitted training labels only; the row's own label updates its state afterwards. Validation and feature-only submission rows use the completed training state and their labels are neither required nor read.

### Inputs / Workload

Full KuaiRand-Pure train/validation rows, seeds 0–4, and the provisional organizer evaluator hash `ecfde28392eb14fec4f488083251df50624e1af2b86278b962daecfb42d195de`. The fixed offline planner used zero LLM tokens and the run took `97.71` CPU seconds with zero GPU seconds and zero recorded manual interventions.

### Metrics

| Metric | BPR R003 | EXP-016 | Delta |
|---|---:|---:|---:|
| GAUC | 0.669535 | 0.669419 | -0.000116 |
| nDCG@5 | 0.536628 | 0.536450 | -0.000178 |
| primary | 0.603082 | 0.602934 | -0.000148 |

Population standard deviation for primary was `0.000348`. The selected best seed (2) had validation primary `0.603398`; it is frozen only as the experiment's reproducible artifact, not selected over the multi-seed decision.

### Correctness Validation

Synthetic tests prove strict-prior construction and frozen, label-free evaluation state. The full suite passed 45 tests before execution. The runtime ordering audit found `22,725` changed pairwise relations across `6,576` of `18,460` eligible validation users, proving this candidate-specific field actually changes within-user ordering. The frozen best checkpoint generated `170,588` aligned test rows plus header at `artifacts/submissions/exp-016-provisional.csv` (SHA-256 `d85837a9e7829a7325b4809eb44b89138f3144bec3ae215d5bf69bf67dac9ffa`) without test scoring or test-label access.

### Interpretation

The intended mechanism is active but does not improve the declared multi-seed BPR comparison. The scale item×tab result therefore does not transfer automatically to this Pure FM representation. Retain R022 as a negative result and do not make it a parent or ensemble component.

### Limitations

This remains validation-only evidence under the provisional starter evaluator; REQ-014 organizer clarification is still required before any final metric-specific selection or official-bonus claim.

### Reproduction

`.venv/bin/python -m tiktok_ml_agent autonomous-item-tab-history --repository-root . --starter-kit kuairand-starter-kit --data-dir kuairand-starter-kit/KuaiRand-Pure/data --parent-ledger artifacts/autonomous-ranking-verified/ledger.sqlite --output-dir artifacts/autonomous-item-tab-history`

## R021 - Frozen KuaiRand-27K item×tab blend grid

Date: 2026-08-28
Experiment: EXP-015
Implementation / commit: `d5bb038`

### Change Tested

Without refitting, evaluated a predeclared symmetric grid of item-rate weights `{0.25, 0.50, 0.75}` against the same frozen model SHA-256 `ea947081e440d8a3266d03b6c03ba25f00ca546424b750c08453eb7c155dfc58`. Each setting streamed all 71,149,570 validation rows through the same evaluator/shard protocol.

### Metrics

| Item weight | GAUC | nDCG@5 | primary |
|---:|---:|---:|---:|
| 0.25 | 0.572022 | 0.587229 | 0.579626 |
| **0.50** | **0.574100** | **0.599412** | **0.586756** |
| 0.75 | 0.573556 | 0.591308 | 0.582432 |

### Interpretation

The middle weight is selected within this declared three-point grid. It is exactly R020's checkpointed configuration, so the selected 27K output remains bound to the frozen model and output hash recorded there. The grid consumes validation feedback and is retained for transparency; the result remains provisional pending organizer contract clarification and is not a hidden-test claim.

## R020 - Checkpointed KuaiRand-27K item×tab output

Date: 2026-08-28
Experiment: EXP-015
Implementation / commit: `f232324`

### Revalidation and frozen artifact

Repeated R018's exact configuration after adding the required scale-checkpoint path. The persisted model `artifacts/scale/kuairand-27k-item-tab-model.npz` has SHA-256 `ea947081e440d8a3266d03b6c03ba25f00ca546424b750c08453eb7c155dfc58`; its full validation result reproduced R018 exactly: GAUC `0.574100`, nDCG@5 `0.599412`, primary `0.586756` over 71,149,570 rows. The checkpointed pass took 523.55 seconds.

### Feature-only output validation

Generated `artifacts/submissions/kuairand-27k-item-tab.csv` by loading that frozen model—without refitting or test-label access. The CSV has the provisional header `row_id,user_id,video_id,score`, exactly 114,832,240 lines (one header plus every one of R016's 114,832,239 test rows), and final row id `114832238`. Its SHA-256 is `c4e95a9702ffc61dbbf5e2a369d3902df7945d40efb033a4c9ad2caaac37fcc5`.

### Interpretation

The scale checkpoint→validation→feature-only-output chain is now demonstrated end to end on the full 27K artifact. It remains an internal/provisional evaluation artifact: no local test score was computed, no final campaign designation has occurred, and organizer metric clarification is still required for a final official claim.

## R019 - KuaiRand-1K item×tab robustness result

Date: 2026-08-28
Experiment: EXP-015
Implementation / commit: `d061167`

### Change Tested

Ran the exact same declared 24-bit item/item×tab (`0.5/0.5`) rate blend as R018 on the official 1K artifact. It used only 1K training labels and the same provisional evaluator/sharded validation policy.

### Metrics

| Metric | Item-only R012 | Item×tab R019 | Delta |
|---|---:|---:|---:|
| GAUC | 0.542570 | 0.542923 | +0.000354 |
| nDCG@5 | 0.545226 | 0.548764 | +0.003538 |
| primary | 0.543898 | 0.545843 | +0.001946 |

The full 2,524,980-row validation pass took 18.76 seconds and exposed no test labels.

### Interpretation

The tab cross's improvement direction is consistent across 1K and 27K, though its magnitude differs. This supports the mechanism as a scale candidate but does not make 1K a selection proxy or establish an organizer leaderboard threshold.

## R018 - KuaiRand-27K bounded item×tab improvement

Date: 2026-08-28
Experiment: EXP-015
Implementation / commit: `d061167`

### Change Tested

Added a second fixed 24-bit hashed rate table for `video_id × tab`, where tab is an inference-known impression field. The model blends smoothed item and item×tab long-view rates equally (`0.5/0.5`) after fitting both tables only on the 136,296,576 training rows. It uses 33,554,432 total counter slots and the identical 256-shard validation/evaluator protocol as R017.

### Metrics

| Metric | Item-only R017 | Item×tab R018 | Delta |
|---|---:|---:|---:|
| GAUC | 0.570914 | 0.574100 | +0.003186 |
| nDCG@5 | 0.544153 | 0.599412 | +0.055259 |
| primary | 0.557534 | 0.586756 | +0.029223 |

The full 71,149,570-row validation pass took 526.90 seconds, used no GPU-hours or LLM tokens, and never read test labels.

### Interpretation

The inference-known tab cross substantially improves the bounded scale baseline, especially top-five ranking. This is a validation-only result under the provisional Pure evaluator; it is not an organizer 27K reference comparison, hidden-test result, or proof that any official bonus threshold has been beaten. Preserve it as the current 27K validation parent and test its robustness before designation.

## R017 - KuaiRand-27K bounded streaming popularity baseline

Date: 2026-08-28
Experiment: EXP-011
Implementation / commit: `35d5b8d`

### Change Tested

Trained a one-pass, fixed-memory 24-bit hashed long-view popularity table on all 136,296,576 training rows. The model uses 16,777,216 counter slots rather than retaining the full item-ID universe. Validation was written into 256 user-consistent temporary shards and each shard delegated its metric calculation to the supplied evaluator; the aggregate uses that evaluator's documented GAUC positive-weighting and nDCG user-weighting. No test label was indexed, materialized, or scored.

### Metrics

| Metric | Value |
|---|---:|
| GAUC | 0.570914 |
| nDCG@5 | 0.544153 |
| primary | 0.557534 |
| validation rows | 71,149,570 |
| validation users | 26,729 |
| wall seconds | 431.83 |

### Interpretation

This completes a full bounded-memory train/validation run on the official 27K artifact. It is a scale/integrity baseline using the provisional Pure evaluator, not an organizer-provided 27K reference or hidden-test result. It therefore does not establish that the bonus benchmark has been beaten; further comparable 27K candidates and organizer-contract confirmation remain required.

## R016 - KuaiRand-27K official artifact preflight

Date: 2026-08-28
Experiment: EXP-011
Implementation / commit: `4697247`

### Dataset Integrity

The official `KuaiRand-27K.tar.gz` archive was downloaded and verified against the published MD5 `3e3c799a24e2d23a4d2c757fbf9adf59`. One-pass source-order preflight (`one-pass-source-order-v2`) identified 136,296,576 train rows, 71,149,570 validation rows, and 114,832,239 test rows across the four official dated log shards. The feature-only test fingerprint is `9eabadd1f15369e681f34cbdbd83b0c309352b4d71fb050f005b771f4b0bf4c9`.

### Interpretation

The bonus artifact is available and its streaming split boundary is demonstrated. This is not a model metric or an organizer 27K benchmark result. The bounded validation baseline is running separately and no test `long_view` value was indexed, materialized, or scored.

## R015 - Top-five-aware Lambda-BPR result

Date: 2026-08-28
Experiment: EXP-014
Implementation / commit: `101c41a`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Change Tested

Retained same-user BPR pairs, fields, optimizer, split, and five seeds. Added an equal mixture of ordinary BPR loss and detached nDCG@5 swap-gain-weighted BPR loss, where non-zero weight occurs only when a sampled pair can change the current top-five discounted gain.

### Metrics

| Metric | Mean | Population std | Delta vs BPR |
|---|---:|---:|---:|
| GAUC | 0.667510 | 0.000494 | -0.002025 |
| nDCG@5 | 0.535785 | 0.000301 | -0.000844 |
| primary | 0.601647 | 0.000326 | -0.001434 |

The autonomous run used 121.20 CPU seconds, zero GPU-hours, zero LLM tokens, and zero manual interventions. The best seed changed 50,819 eligible within-user pairwise relations for 9,836 of 18,460 users relative to BPR.

### Interpretation

This fixed 50/50 Lambda-BPR mixture is materially worse than BPR on both component metrics. The failure is retained as evidence that direct top-five weighting needs a different calibration or mechanism before another attempt; it is rejected as a parent and excluded from the current ensemble.

## R014 - Three-negatives-per-positive BPR sampling result

Date: 2026-08-28
Experiment: EXP-013
Implementation / commit: `9f5a88b`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Change Tested

Retained the BPR loss, FM fields, optimizer, data split, and five seeds but sampled three strictly same-user negatives for every positive rather than one.

### Metrics

| Metric | Mean | Population std | Delta vs BPR |
|---|---:|---:|---:|
| GAUC | 0.669069 | 0.000999 | -0.000465 |
| nDCG@5 | 0.536571 | 0.000418 | +0.000006 |
| primary | 0.602820 | 0.000693 | -0.000262 |

The run used 120.61 CPU seconds, zero GPU-hours, zero LLM tokens, and zero manual interventions. Its best seed altered 41,313 eligible within-user pairwise relations for 8,992 of 18,460 users relative to the BPR parent.

### Interpretation

The denser sampler did not translate to a useful mean ranking improvement and increased variance. Reject it as a parent; retain the full checkpoint, event ledger, and measured failure as a sampling-family result.

## R013 - Train-only watch-completion BPR result

Date: 2026-08-28
Experiment: EXP-007
Implementation / commit: `1e48fbd`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Change Tested

Added one auxiliary completion head to BPR FM. Its target was `clip(play_time_ms / duration_ms, 0, 1)` from training rows only. Validation and test row objects cannot request `play_time_ms`; the evaluated score stayed the primary long-view BPR logit.

### Metrics

| Metric | Mean | Population std | Delta vs BPR |
|---|---:|---:|---:|
| GAUC | 0.669489 | 0.000607 | -0.000045 |
| nDCG@5 | 0.536557 | 0.000418 | -0.000008 |
| primary | 0.603023 | 0.000491 | -0.000059 |

The autonomous run used 105.44 CPU seconds, zero GPU-hours, zero LLM tokens, and zero manual interventions. The best watch-time seed changed 44,299 eligible within-user pairwise relations for 9,088 of 18,460 users relative to the frozen BPR parent, so the candidate was not user-constant or inert.

### Interpretation

This first completion-auxiliary configuration is a small regression and is rejected as a parent. Its complete ledger, recovered audit event, checkpoint manifests, and prediction files are retained. It did not access validation or test watch-time outcomes.

## R012 - KuaiRand-1K streaming popularity bonus baseline

Date: 2026-08-28
Experiment: EXP-010
Implementation / commit: `305b057`

### Purpose

Validate that the agent can train and evaluate a real bonus-scale artifact without loading its test labels or relying on the Pure in-memory path.

### Dataset Integrity

The official `KuaiRand-1K.tar.gz` archive was downloaded from Zenodo and verified against MD5 `6b0b9c8222d67fcd4c676218edca3f1f`. Streaming preflight found 5,055,984 train, 2,524,980 validation, and 4,132,081 test rows. Test rows were exposed as features/identifiers only.

### Change Tested

One-pass smoothed item long-view popularity, trained on 2,119,510 unique training items and evaluated with the provisional organizer evaluator on the 1K validation time range.

### Metrics

| Metric | Value |
|---|---:|
| GAUC | 0.542570 |
| nDCG@5 | 0.545226 |
| primary | 0.543898 |
| wall seconds | 16.54 |

### Interpretation

This is a scalable integrity and baseline result, not a comparison against an organizer-provided 1K reference. The metric profile remains provisional under REQ-014, but the data adapter, streaming train/evaluate path, and feature-only test boundary are now demonstrated on the official bonus artifact.

## R011 - Compact DeepFM BPR backbone result

Date: 2026-08-28
Experiment: EXP-012
Implementation / commit: `efa568e`

### Change Tested

Replaced the FM scoring backbone with a compact DeepFM-style model: the original FM interactions plus a 64-unit nonlinear tower over the same field embeddings. BPR, categorical fields, data split, early stopping, and seeds remained controlled.

### Metrics

| Metric | Mean | Population std | Delta vs BPR | Delta vs R010 |
|---|---:|---:|---:|---:|
| GAUC | 0.669561 | 0.001082 | +0.000027 | -0.001283 |
| nDCG@5 | 0.536668 | 0.000460 | +0.000040 | -0.000520 |
| primary | 0.603115 | 0.000736 | +0.000033 | -0.000902 |

### Interpretation

The nonlinear tower does not deliver a useful mean gain at this scale and substantially increases seed variance. Reject this 64-unit DeepFM configuration as a parent. Its retained artifact remains available only for future frozen-ensemble analysis, not as a selected component.

## R010 - Three-component frozen rank ensemble improvement

Date: 2026-08-28
Experiment: EXP-009A (child of EXP-009)
Implementation / commit: `f63f617`

### Change Tested

Added the frozen inference-known temporal BPR predictor to the R008 BPR/history rank ensemble. Four predeclared three-weight vectors were evaluated across the same five seed-aligned validation predictions. The selected vector was `0.375` BPR, `0.375` history, and `0.25` temporal.

### Metrics

| Metric | Mean | Population std | Delta vs R001 baseline | Delta vs R008 |
|---|---:|---:|---:|---:|
| GAUC | 0.670845 | 0.000685 | +0.003444 | +0.000432 |
| nDCG@5 | 0.537188 | 0.000240 | +0.001445 | +0.000070 |
| primary | 0.604017 | 0.000441 | +0.002444 | +0.000251 |

The other declared grid means ranged from `0.603866` to `0.603954`.

### Correctness Validation

All three components are frozen checkpoint manifests. The composite manifest includes component weights, full grid, best validation prediction hash, data and evaluator hashes, and it generated a schema-valid 170,588-row output without test scoring.

### Interpretation

R010 is the current validation leader. Its improvement over R008 is smaller than epsilon, so it does not reset a global epsilon/N convergence counter by itself; it should nevertheless remain the scored candidate rather than being discarded.

## R009 - Inference-known weekday-cross BPR result

Date: 2026-08-28
Experiment: EXP-008
Implementation / commit: `9235cd9`

### Change Tested

Added one weekday categorical field derived only from each impression's known calendar date. It crosses with candidate fields inside BPR FM and uses no post-exposure or validation outcome.

### Metrics

| Metric | Mean | Population std | Delta vs BPR | Delta vs R008 ensemble |
|---|---:|---:|---:|---:|
| GAUC | 0.670019 | 0.000365 | +0.000484 | -0.000393 |
| nDCG@5 | 0.536993 | 0.000208 | +0.000364 | -0.000125 |
| primary | 0.603506 | 0.000270 | +0.000424 | -0.000259 |

The validation early/late primary means were `0.590071` and `0.561413` respectively (gap `0.028658`). This is a drift diagnostic, not a second validation metric or selection gate.

### Interpretation

The temporal feature improves standalone BPR but does not exceed the frozen ensemble. Keep its prediction artifact available for a later declared ensemble comparison; do not promote it as the current parent.

## R008 - Frozen BPR/history rank ensemble improvement

Date: 2026-08-28
Experiment: EXP-009
Implementation / commit: `597c936d23e066d3cc7d890b19dfc8c9222210e4`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Question

Can a rank-space blend of the frozen BPR and leakage-safe history-cross components improve validation primary without retraining either model?

### Change Tested

For each seed, percentile-ranked BPR and history scores were blended. The declared BPR-weight grid was `{0.25, 0.50, 0.75}` and the five-seed mean selected `0.25` BPR / `0.75` history. Component checkpoint manifests and validation predictions were preserved.

### Metrics

| Metric | Mean | Population std | Delta vs R001 baseline |
|---|---:|---:|---:|
| GAUC | 0.670412 | 0.000547 | +0.003012 |
| nDCG@5 | 0.537118 | 0.000243 | +0.001374 |
| primary | 0.603765 | 0.000332 | +0.002193 |

The other declared blend means were `0.603699` at BPR weight `0.50` and `0.603569` at `0.75`.

### Correctness Validation

No component was retrained. The ensemble manifest binds both source manifests, the selected weight, validation-prediction hash, code, data, and evaluator hashes. It generated a schema-valid, 170,588-row test output from the component checkpoints without test scoring.

### Interpretation

This is the first candidate exceeding the provisional `epsilon=0.002` improvement threshold over R001. It is a validation-only result and not a converged final claim; the weight grid consumed validation feedback and must remain visible in the report.

### Decision / Next Step

Use the frozen ensemble as the current research parent and judge later candidates against it using the global convergence ledger.

## R007 - Multi-feedback BPR regression

Date: 2026-08-28
Experiment: EXP-006
Implementation / commit: `92658323a126dee65d6b31bbdbe2e1f1bc12b83a`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Question

Do train-only click, like, and follow auxiliary tasks improve a shared FM representation for the primary long-view BPR ranker?

### Baseline

EXP-004A BPR five-seed mean primary `0.603082`.

### Change Tested

Added three task-specific bias heads above one shared FM. The primary head retained BPR on long-view; click, like, and follow used auxiliary BCE from training rows only, with auxiliary weight `0.15`. Validation exposes no auxiliary outcome labels.

### Metrics

| Metric | Mean | Population std | Delta vs BPR |
|---|---:|---:|---:|
| GAUC | 0.668488 | 0.000725 | -0.001046 |
| nDCG@5 | 0.536108 | 0.000497 | -0.000521 |
| primary | 0.602298 | 0.000571 | -0.000783 |

The autonomous five-seed run consumed `118.22` CPU seconds, no GPU-hours, no LLM tokens, and no manual interventions.

### Correctness Validation

Unit tests confirm auxiliary-head gradients update independently. The safe loader blocks auxiliary outcomes outside the training split. The run is checkpoint-backed and validation-only.

### Interpretation

This first multi-task weighting is a regression. The result does not reject multi-task learning universally, but it rejects this architecture/weight as a parent.

### Decision / Next Step

Do not tune against one seed. Any future multi-task retry must change one named mechanism (task weighting, gradient balancing, or a richer head) and run the same multi-seed protocol.

## R006 - Checkpoint-parented history-cross BPR result

Date: 2026-08-28
Experiment: EXP-005
Implementation / commit: `e71322a7a413212e1bd13aaa652f14a6020f39e7`
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Question

Can a strictly earlier train-only long-view history field improve BPR FM ranking through interactions with candidate features?

### Baseline

R003 / EXP-004A five-seed BPR mean primary `0.603082`.

### Change Tested

Added a categorical user-history bucket encoding prior training-period long-view count and rate. Each training event sees only prior event labels; every validation feature is frozen from the completed training period. The bucket is an FM field, so its only route to reorder a user's candidates is through crosses with video, author, tab, and duration.

### Inputs / Workload

Full train/validation data, seeds 0–4. The autonomous runner loaded the immutable EXP-004A checkpoint manifest, generated a new checkpoint per seed, and used only the organizer validation evaluator.

### Metrics

| Metric | Mean | Population std | Delta vs BPR |
|---|---:|---:|---:|
| GAUC | 0.669741 | 0.000517 | +0.000206 |
| nDCG@5 | 0.536777 | 0.000256 | +0.000148 |
| primary | 0.603259 | 0.000319 | +0.000177 |

The run used `87.89` CPU seconds, `0` GPU-hours, and `0` LLM tokens because this was the deterministic offline policy mode.

### Correctness Validation

Automated tests establish strict-prior training history and train-only frozen validation history. The runtime ordering audit found `24,282` changed pairwise relations across `6,758` of `18,460` eligible validation users, so the field affects within-user ranking. No hidden-test scoring occurred.

The frozen best-seed checkpoint generated `170,588` aligned test rows plus header through `tiktok_ml_agent submission`; the adapter checked header, row IDs, user/video alignment, and finite scores without scoring test labels.

### Interpretation

The history cross is mechanism-valid and positive but its mean gain is materially smaller than the provisional `epsilon=0.002`. Retain it as a component candidate; do not declare it a promoted final parent or a converged improvement.

### Limitations

Only one aggregate history representation was tested. The automated policy was deterministic and therefore consumed no LLM tokens; a provider-backed planner remains an optional, unexercised integration.

### Decision / Next Step

Explore candidate-specific temporal similarity or multi-feedback only through the same frozen-parent, ordering-audit, five-seed protocol.

### Reproduction

`python -m tiktok_ml_agent autonomous-history --parent-ledger artifacts/autonomous-ranking-verified/ledger.sqlite --output-dir artifacts/autonomous-history-verified`

## R005 - Recovered history-audit execution failure

Date: 2026-08-28
Experiment: EXP-005
Implementation / commit: `242fbc8`

### Question

Does the autonomous recovery path retain an unexpected runtime failure without converting it into a model result?

### Result

The initial history-audit candidate trained all five validation seeds, then raised `NameError: name 'np' is not defined` while loading the parent prediction artifact for its final ordering audit. The controller finalized it as `recovered` with recovery action `revert_candidate_worktree_to_immutable_parent`; it has no metrics or checkpoint manifest and is not used for selection.

### Decision / Next Step

Added the missing import and a regression test that mocks the execution path through the parent-prediction audit. R006 is the subsequent successful rerun. This failure remains recorded as autonomy/recovery evidence.

## R004 - Exact per-user listwise FM regression

Date: 2026-08-28
Experiment: EXP-004
Implementation / commit: uncommitted `arjun-t2-002-foundation` worktree
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Question

Does an exact full-impression-list softmax objective improve the organizer within-user ranking metrics without negative sampling?

### Baseline

R002 PyTorch pointwise FM control, five-seed validation primary mean `0.601622`.

### Change Tested

Replaced BCE with a per-user exact listwise softmax loss. Each training update retained complete logged impression groups; no negative pair sampling was used.

### Inputs / Workload

Full train/validation data, seeds 0–4, train/validation-only adapter.

### Metrics

| Metric | Mean | Sample std | Delta vs NumPy baseline |
|---|---:|---:|---:|
| GAUC | 0.662623 | 0.000230 | -0.004777 |
| nDCG@5 | 0.533989 | 0.000123 | -0.001755 |
| primary | 0.598306 | 0.000164 | -0.003266 |

Every paired seed was below the NumPy baseline. Mean wall time was `18.358` seconds per seed.

### Correctness Validation

Unit tests verified complete user-group batches and lower listwise loss when positives are ranked above negatives. No hidden-test scoring occurred.

### Interpretation

The exact listwise formulation is a stable regression under this implementation and configuration. The outcome is retained as a negative finding; future listwise work requires a materially different objective or weighting rationale.

### Limitations

Only one listwise formulation and hyperparameter setting were tested.

### Decision / Next Step

Reject this exact-listwise configuration as a parent. Preserve the evidence card for planner retrieval.

### Reproduction

`for seed in 0 1 2 3 4; do .venv/bin/python -m tiktok_ml_agent ranking-valid --objective listwise --seed "$seed"; done`

## R003 - BPR ranking-loss FM improvement

Date: 2026-08-28
Experiment: EXP-004
Implementation / commit: uncommitted `arjun-t2-002-foundation` worktree
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU.

### Question

Does within-user BPR training improve the organizer ranking metrics relative to pointwise FM?

### Baseline

R001 organizer-compatible NumPy FM five-seed validation primary mean `0.601572`; R002 PyTorch pointwise control mean `0.601622`.

### Change Tested

Replaced pointwise BCE with BPR. For every eligible user, the sampler draws one same-user negative for each positive impression. The model, fields, learning rate, batch size, patience, and validation evaluator remain otherwise controlled.

### Inputs / Workload

Full train/validation data, seeds 0–4, train/validation-only adapter.

### Metrics

| Metric | Mean | Sample std | Delta vs NumPy baseline |
|---|---:|---:|---:|
| GAUC | 0.669535 | 0.000538 | +0.002134 |
| nDCG@5 | 0.536629 | 0.000289 | +0.000885 |
| primary | 0.603082 | 0.000350 | +0.001510 |

The mean primary delta versus the PyTorch pointwise control is `+0.001459`. Mean wall time was `18.214` seconds per seed.

### Correctness Validation

Unit tests assert that sampled positive/negative indices always belong to the same user. The organizer evaluator was called only on validation labels.

### Interpretation

The BPR objective improves both GAUC and nDCG@5 across the five-seed mean. The improvement is promising but smaller than the provisional convergence epsilon `0.002`; it should be treated as a new research parent, not as a final claim.

### Limitations

The pairing strategy, loss weight, learning rate, and model architecture are not yet tuned. This is validation-only evidence.

### Decision / Next Step

Promote BPR as a parent for ranking-loss and history-cross experiments. Keep pointwise PyTorch as its control.

### Reproduction

`for seed in 0 1 2 3 4; do .venv/bin/python -m tiktok_ml_agent ranking-valid --objective bpr --seed "$seed"; done`

## R002 - PyTorch pointwise FM parity against the organizer NumPy FM

Date: 2026-08-28
Experiment: EXP-002
Implementation / commit: uncommitted `arjun-t2-002-foundation` worktree
Environment: CPython 3.13.11, NumPy 2.5.2, PyTorch 2.13.0, CPU; MPS was available but deliberately not used for parity.

### Question

Can the PyTorch pointwise FM reproduce the organizer NumPy FM closely enough that later loss changes are attributable to the loss rather than a framework port?

### Baseline

R001 five-seed safe NumPy FM reproduction.

### Change Tested

PyTorch FM with the same five categorical fields, FM interaction equation, explicit Adam-like updates, learning rate, regularization, batching, early stopping, and seed schedule. Training and validation used only permitted train/valid rows.

### Inputs / Workload

Seeds 0–4, full KuaiRand-Pure training split and official validation split. No hidden-test labels or local test scoring were used.

### Metrics

| Metric | NumPy mean | PyTorch mean | Delta |
|---|---:|---:|---:|
| GAUC | 0.667400 | 0.667450 | +0.000050 |
| nDCG@5 | 0.535744 | 0.535794 | +0.000050 |
| primary | 0.601572 | 0.601622 | +0.000050 |

Paired primary deltas for seeds 0–4 were `[-0.000597, +0.000392, +0.000835, +0.000449, -0.000828]`. The mean absolute gap was `0.000050`, below the `0.001` parity gate, and signs were mixed rather than consistently directional.

### Correctness Validation

Fixed-weight logits and BCE matched the organizer implementation within numerical tolerance. A one-update state comparison matched FM embedding, linear, and bias updates within tolerance. Ten unit tests passed before full-data execution.

### Interpretation

Parity Gate A and Gate B pass. The PyTorch pointwise control is eligible as the parent/control for ranking-loss experiments. The observed small residual is recorded rather than hidden.

### Limitations

This is validation-only evidence. It does not prove a hidden-test score or an MPS-accelerated result.

### Decision / Next Step

Proceed to EXP-004 ranking-objective siblings while retaining the pointwise PyTorch control.

### Reproduction

`for seed in 0 1 2 3 4; do .venv/bin/python -m tiktok_ml_agent torch-baseline-valid --seed "$seed"; done`

## R001 - Organizer NumPy FM validation reproduction

Date: 2026-08-28
Experiment: EXP-001
Implementation / commit: uncommitted `arjun-t2-002-foundation` worktree
Environment: CPython 3.13.11, NumPy 2.5.2, CPU.

### Question

Does the safe train/validation-only runner reproduce the organizer FM validation reference without using locally available test labels?

### Baseline

Organizer-published validation primary reference: 0.6016.

### Change Tested

No model change. The runner imports the organizer FM class but replaces the starter runner because the starter runner loads and locally scores test labels.

### Inputs / Workload

Official KuaiRand-Pure archive downloaded from Zenodo. Published MD5 verified: `0820331067a3784d9691136f772b35a7`. Full train rows (1,141,112) and validation rows (124,909), seeds 0–4. No hidden-test scoring.

### Metrics

| Metric | Mean | Sample std |
|---|---:|---:|
| GAUC | 0.667400 | 0.000350 |
| nDCG@5 | 0.535744 | 0.000427 |
| primary | 0.601572 | 0.000353 |
| wall seconds per seed | 16.976 | 1.933 |

Per-seed primary values: `0.601469`, `0.601761`, `0.601090`, `0.601503`, `0.602037`.

### Correctness Validation

The mean primary differs from the organizer validation reference by `-0.000028`. The safe adapter denied test-label access in unit tests and the baseline runner exposes only train/validation labels.

### Interpretation

The organizer FM validation baseline is reproduced closely enough to establish a trustworthy starting point.

### Limitations

The organizer hidden-test reference was intentionally not reproduced or locally scored. The local result is validation evidence only.

### Decision / Next Step

Use this as the baseline for parity and ranking-objective experiments.

### Reproduction

`for seed in 0 1 2 3 4; do .venv/bin/python -m tiktok_ml_agent baseline-valid --seed "$seed"; done`

## RXXX - Result title

Date:
Experiment:
Implementation / commit:
Environment:

### Question

### Baseline

### Change Tested

### Inputs / Workload

### Metrics

### Results

| Metric | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| | | | |

### Correctness Validation

### Interpretation

### Limitations

### Decision / Next Step

### Reproduction
