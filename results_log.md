# Results log

This is the permanent empirical record. Preserve negative results and never record hypotheses as measured outcomes.

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
