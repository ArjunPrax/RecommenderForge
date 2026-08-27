# Handoff log

Newest entries appear first. Record meaningful changes, why they happened, validation, unresolved issues, and useful handoff context.

## 2026-08-28 - Campaign-level convergence accounting

### Changed

Added a persistent campaign convergence model that evaluates epsilon/N across complete candidate batches, records the significant-improvement anchor separately from the best measured run, and exports a machine-readable campaign status.

## 2026-08-28 - Three-component ensemble measured

### Measured

EXP-009A selected BPR/history/temporal weights `0.375/0.375/0.25` with mean validation primary `0.604017`, +`0.002444` over R001 and +`0.000251` over the two-component R008 blend. A schema-valid output was generated from the composite manifest without test scoring.

## 2026-08-28 - Temporal cross measured

### Measured

EXP-008's inference-known weekday cross reached mean validation primary `0.603506`: better than standalone BPR but below R008's frozen ensemble. Early/late validation stability is now recorded in the run diagnosis.

## 2026-08-28 - Frozen rank ensemble measured

### Measured

EXP-009 selected a 0.25 BPR / 0.75 history percentile-rank blend across a predeclared five-seed grid. Its mean validation primary is `0.603765`, +`0.002193` over the reproduced NumPy FM. A schema-valid 170,588-row output was generated from the composite manifest without test scoring.

### Caveat

This is not a converged or hidden-test result. Weight selection uses validation feedback and its full grid is retained in the ensemble manifest and R008.

## 2026-08-28 - Frozen-component ensemble lane

### Changed

Added EXP-009 rank-space blending over the immutable BPR and history-cross validation predictions. The runner evaluates a predeclared five-seed weight grid, freezes the selected component manifest composition, and never retrains a component.

## 2026-08-28 - Controller-integrated isolated candidate executor

### Changed

The controller now accepts run-aware executors. Added a worktree command executor that creates a detached worktree from the immutable parent revision, validates the candidate patch boundary, runs only a host-owned command factory, captures structured result JSON, records the code/diff identity, and removes the worktree after execution.

### Validation

Unit coverage confirms the controller dispatches the run-aware execution route and that the host command result is bound to an isolated candidate lifecycle. No candidate controls the executable command.

## 2026-08-28 - Checkpoint-backed output path

### Changed

Added output generation from a ledger-selected immutable checkpoint. It reconstructs feature vocabularies from train rows, accepts test rows only as feature/identifier records, verifies the checkpoint/evaluator, and validates the resulting Starter Kit schema without invoking any score path.

### Validation

Generated `170,588` EXP-005 test rows plus header from the frozen best-seed checkpoint. Alignment and finite-score checks passed. No model was retrained and no test labels were read or scored.

## 2026-08-28 - Multi-feedback candidate evidence

### Changed

Added train-only access to click/like/follow labels, a shared-FM multi-task BPR candidate, and an autonomous five-seed runner from the immutable BPR parent.

### Measured

EXP-006 mean validation primary was `0.602298`, `-0.000783` relative to BPR. The first shared-FM auxiliary configuration is rejected; see R007. The negative result is preserved rather than tuned away.

### Validation

The multi-task head-gradient and train-only auxiliary-access tests pass. The run wrote an immutable checkpoint manifest and did not access test labels or scores.

## 2026-08-28 - Autonomous ranking and history evidence

### Changed

Ran the checkpoint-backed validation-only EXP-004 objective siblings and EXP-005 history continuation. Added strict-prior/train-only frozen history construction, a runtime within-user ordering-change audit, and a regression test for the audit execution path.

### Measured

- EXP-004A BPR: mean validation primary `0.603082`, +`0.001510` vs R001 NumPy FM.
- EXP-004B exact listwise: mean `0.598306`; retained as a negative result.
- EXP-005 history cross: mean `0.603259`, +`0.000177` vs BPR; changed `24,282` pairwise relations across `6,758` eligible users but is not promoted on its small score delta.
- Initial EXP-005 audit attempt recovered from a missing NumPy import (R005); the fixed rerun is R006. No result was hidden or reused from the recovered run.

### Validation

The latest unit suite has 24 passing tests. Each successful run has code/diff/evaluator/checkpoint/prediction/data hashes in its generated ledger report. All reported metrics use the provisional organizer validation evaluator; no local test scoring was invoked.

## 2026-08-28 - Phase 1 integrity kernel, baseline controls, and first autonomous batch runner

### Changed

Implemented the Track 2 control plane under `src/tiktok_ml_agent/`: versioned benchmark contracts; a safe KuaiRand-Pure loader that does not materialize test labels; organizer-evaluator delegation; append-only SQLite ledger; checkpoint manifests; deterministic recovery and convergence; structured evidence retrieval/memory; bounded planner validation; safe worktree/diff policy; and report export.

Added a deterministic qualification run with a controlled failure and an initial real-benchmark `autonomous-ranking` command. The real command uses a bounded two-sibling ranking-objective plan, five validation seeds per sibling, checkpoint-backed artifacts, and no test scoring route. An optional OpenAI Responses planner boundary is available but not invoked without a user-supplied API key.

Reproduced the validation-only NumPy FM reference, established fixed-weight and five-seed PyTorch pointwise parity, and recorded the first BPR/listwise comparison in `results_log.md`.

### Why

The competition evaluates autonomy, reproducibility, integrity, recovery, and resource evidence in addition to ranking improvement. These components must exist before subsequent research directions can create credible judge-facing evidence.

### Validation

- `python -m compileall -q src tests`
- `python -m unittest discover -s tests -v` — 20 tests passing.
- `git diff --check` — passing.
- Measured results are recorded as R001–R004. No development command scores the test split.

### Unresolved

REQ-014 remains blocked: the current official PDF's narrative metric/label conflicts with the runnable organizer Starter Kit. The provisional long-view/GAUC/nDCG@5 evaluator is versioned and must not be represented as final organizer clarification.

## 2026-08-26 - Plan v3 review disposition and deferred-fork register

### Changed

Added `docs/DEFERRED_FORKS.md`. No code, no dependency, no dataset, and no benchmark work was
performed. The repository remains at the Phase 0 bootstrap state.

The agreed build is **Codex execution plan v3**. Claude's review of v3 raised six refinements plus one
research addition. Their disposition is now recorded, split by whether deferral is safe:

**Apply during the wave they touch - cheap now, expensive or impossible later:**

- FORK-02: Wave 2 exit criteria require recovery, convergence evaluation, and report generation, but
  v3 schedules all three as Wave 3 deliverables. Wave 2 cannot pass as written. Move those three
  components into Wave 1; Wave 3 then adds research-tree selection and reflection on top of a working
  deterministic loop. This defect came from pulling the qualification run earlier - an accepted review
  point whose dependency was not propagated to the wave table.
- FORK-03: Parity Gate B accepts a 0.002 NumPy-to-PyTorch gap. That is `epsilon`, an unrelated
  quantity, and it is roughly half the +0.004 target improvement. Tighten to <= 0.001 (about 2 SE of a
  5-seed mean, given per-seed std 0.0008), add a sign test so a consistently-below-NumPy port is
  treated as a defect rather than noise, and carry any residual gap as a known offset.
- FORK-04: Add `run_class` (qualification | research | designated_final) to `RunRecord`, and state
  explicitly whether qualification-run tokens, compute, and manual interventions count toward the
  reported "resource usage required to reach the converged result".
- FORK-05: `EXP-XXX` numbers were reassigned between plan v2 and v3 (v2 EXP-002 was ranking
  objectives; v3 EXP-002 is PyTorch parity, and everything after shifted). `AGENTS.md` forbids
  recycling IDs. Nothing is burned yet because neither plan was committed. Assign the numbers once in
  Wave 0 and never shift them; append new families at the end.

**Genuinely optional - test only if schedule allows:**

- FORK-01: The inner-development split is doing two jobs. Job A (early stopping and hyperparameter
  selection inside `fit()`, so official validation is not consumed as a training signal) is mandatory
  and correct in v3. Job B (rejecting candidates before they reach official validation) is a fidelity
  proxy and conflicts with v3's own rule that no proxy may reject a candidate without demonstrated
  rank correlation. Recommended default is to keep Job A, drop Job B, and run every candidate at full
  fidelity - full-data FM is ~40 s on one CPU core, so Job B saves nothing at Pure scale.
- FORK-06: At report time, present `GPU-hours = MPS + CUDA` as the single deliverable figure with the
  split shown beneath, so the headline is not understated.
- FORK-07: Evaluation lists average ~7.15 impressions per user on test (170,588 rows / 23,875 users),
  so an exact listwise softmax over a user's full impression list is computable with no negative
  sampling. Promote exact listwise to a first-round ranking-objective candidate alongside BPR rather
  than holding it as a later option.

### Why

To keep the agreed v3 build intact while preserving refinements that would otherwise be lost, and to
separate deferrable ideas from defects that must be fixed in the wave they touch. The distinction
matters: three of the six are not safely deferrable, and recording them as "later" would guarantee
they are hit at the worst moment.

### Impact

No behaviour changed. Codex should treat FORK-02, FORK-03, FORK-04, and FORK-05 as inputs to Wave 0
and Wave 1 rather than as a backlog, and may treat FORK-01, FORK-06, and FORK-07 as optional.

### Validation

Verified against sources rather than asserted:

- Updated official PDF re-extracted and hashed:
  `a940266486f5b3b320f932b4261470c986f47d8d5d9d3f484b645225b9ee82ff`, 12 pages, last updated
  26 August 2026. AliCCP occurs **0** times (13-page predecessor had 14 occurrences). The
  `long_view`/GAUC/nDCG@5 versus `click`/NDCG@10/Recall@50 conflict is confirmed present on p.5 and
  the kit versus pp. 4, 6, 7, 8.
- Baseline figures, `epsilon`/`N`, seed std, split dates, row counts, and submission schema
  cross-checked against `kuairand-starter-kit/baseline_scores.json`, `evaluate.py`, `data.py`, and
  `submit.py`.
- Repository state confirmed at commit `1cdd40c` with no remote divergence; `CLAUDE.md` and
  `docs/handoffs/` do not exist yet, so `changelog.md` remains the handoff mechanism per D003.

Not validated: no dataset was downloaded and no baseline was executed, so every organizer figure
cited remains a **reference value**, not a reproduced measurement.

### Files

`docs/DEFERRED_FORKS.md` (new), `changelog.md`.

### Related

Task: none assigned - this precedes Wave 0. Requirements: REQ-014 (benchmark conflict; AliCCP portion
now resolved by the updated PDF, metric/label portion still open). Decisions: none recorded yet;
Codex owns D006 onward at Wave 0.

### Handoff Notes

`FORK-XX` identifiers are local to `docs/DEFERRED_FORKS.md` and are deliberately **not** `EXP-XXX`,
`T2-XXX`, `DXXX`, or `RXXX`. Codex assigns stable IDs at Wave 0; do not cite `FORK-XX` in commits,
PRs, or `results_log.md`.

`CLAUDE.md`, `docs/WORKBOARD.md`, and `docs/handoffs/` are Codex-owned Wave 0 deliverables and were
deliberately not created here to avoid claiming files another agent owns.

These changes are uncommitted and sit in the working tree on branch `Arjun`. Plan v3 states `Arjun`
should not be used as a shared writable development branch, so this should move to a task branch
before it is committed.

## 2026-08-26 - Phase 0 repository bootstrap

### Changed

Created the Track 2-only scaffold, documentation conventions, collaboration templates, and operating context. No solution architecture, technical stack, prototype, experiment, or implementation was selected.

### Why

To make the repository durable shared memory for two humans and future Codex sessions.

### Impact

Future work follows `AGENTS.md`. The PDF's conflicting required-benchmark statements are explicitly unresolved.

### Validation

Validated local structure with `git diff --check`. Created `ArjunPrax/TiktokTechjamTrack2` as a private GitHub repository and verified its private-only settings. Bootstrap commit `5d61ceb` was pushed to `main`.

### Files

Bootstrap files and `docs/`.

### Related

Task: T2-001. Decisions: D001-D005.

### Handoff Notes

Do not begin technical planning before the human advances past Phase 0. Seek organizer clarification for REQ-014.
