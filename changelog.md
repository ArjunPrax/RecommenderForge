# Handoff log

Newest entries appear first. Record meaningful changes, why they happened, validation, unresolved issues, and useful handoff context.

## 2026-08-30 - Public-checkout CI repair

### Changed

The integrity workflow now names and tests its actual contract: a public checkout without organizer materials. Tests that prove parity against the local organizer evaluator or baseline now skip only when those deliberately untracked files are absent; all data-free safety, controller, ledger, and model tests still execute.

### Validation

The first remote CI attempt exposed the missing-file assumption rather than a product failure. With the local organizer kit present, `uv lock --check`, the complete 71-test suite, and `git diff --check` pass. The repaired workflow is awaiting its public-checkout reproduction and GitHub rerun.

### Related

Task: T2-014. Result: R033. Requirements: REQ-003, REQ-006, REQ-011, REQ-017.

## 2026-08-30 - Final rubric and delivery-contract audit

### Changed

Added a source-by-source final delivery audit and promoted the public three-minute YouTube demo to an explicit mandatory release gate. The audit records the durable PDF/Starter-Kit metric contradiction, result limitations, required Devpost deliverables, final checkpoint/output hashes, and the conservative redistribution scope.

### Validation

R032 records the review of the official Track PDF, official Devpost event page, local Starter Kit license files, R027 evidence, and current release branch. The local data carries CC BY-SA 4.0 text; Starter Kit source has no separate code-license notice. Neither is tracked or will be published. The actual public video and remote CI are **Not yet demonstrated**.

### Related

Task: T2-013. Result: R032. Requirements: REQ-001–REQ-020.

## 2026-08-29 - Data-free CI integrity gate

### Changed

Added a least-privilege GitHub Actions workflow for every push and pull request. It uses the lockfile, runs the full data-free unit suite, and checks whitespace errors; it does not fetch competition data. A local contract test protects the required workflow commands.

### Validation

Workflow YAML parsing and `uv lock --check` passed; the latter resolved 32 locked packages. The complete local suite passes 71 tests. Remote Actions execution is **Not yet demonstrated** until the reviewed branch is pushed.

### Related

Task: T2-012. Result: R031. Requirements: REQ-003, REQ-006, REQ-011, REQ-017.

## 2026-08-29 - Release-integrity audit

### Validation

R030 records a tracked-content audit before human publication review. `git fsck --no-reflogs --full` found no object-integrity errors (only normal unreachable dangling trees). No tracked competition assets, generated outputs, credentials, or private-key signatures were found; the only matching tracked paths are `.env.example` and `artifacts/.gitkeep`. No files were deleted or rewritten.

### Related

Task: T2-011. Result: R030. Requirements: REQ-007, REQ-011.

## 2026-08-29 - Starter Kit publication isolation

### Changed

The entire separately supplied `kuairand-starter-kit/` directory is now ignored—not only its dataset folders—so a broad Git add cannot publish organizer source before its redistribution terms are verified. README setup now distinguishes obtaining the kit from downloading a dataset archive; provenance and release documentation retain the human authorization gate.

### Validation

Added a repository-safety test and confirmed `git check-ignore -v --no-index kuairand-starter-kit/evaluate.py` resolves to the new whole-directory rule. The complete suite passes 70 tests. R029 records this as repository-safety evidence, not redistribution permission.

### Related

Task: T2-010. Result: R029. Requirements: REQ-007, REQ-011.

## 2026-08-29 - Real isolated child-process recovery proof

### Changed

Added T2-009's integration test for the controller's existing wall-clock recovery path. It creates a temporary Git repository, runs a trusted child through the real disposable-worktree executor, and gives it a one-second budget. The child writes its PID before sleeping so cleanup can be observed directly.

### Validation

The child requested ten seconds of sleep but the controller returned in `1.110` seconds with a ledgered `TimeoutError` recovery. The test proves that the child PID no longer exists and that the disposable worktree has been removed from both the filesystem and Git's worktree list. The complete suite passes 69 tests. It does not access competition data or labels. R028 retains the measured resilience evidence.

### Related

Task: T2-009. Result: R028. Requirements: REQ-006, REQ-009, REQ-019.

## 2026-08-29 - Public-deliverable setup and provider-boundary verification

### Changed

Added concrete `uv` setup and dataset-placement instructions plus an explicit limitations section to the README. Corrected the problem-source note so it describes D029/D031's team interpretation without incorrectly claiming organizer confirmation.

### Validation

Added a mocked Responses-API planner test that verifies the bounded JSON proposal is schema-validated, response token usage and response ID are retained, and an API key is not embedded in the request body. It makes no network request or token-consuming provider call. The full suite now passes 68 tests.

### Related

Requirements: REQ-001, REQ-005, REQ-011, REQ-013, REQ-019. This does not change the measured campaign's honest zero-token record.

## 2026-08-29 - Team-interpreted final designation and output chain

### Changed

D031 adds an explicit `team_interpreted` campaign status between fail-closed `provisional` and organizer-`confirmed`. A team-interpreted campaign may bind its converged frozen checkpoint, but the status is retained in the campaign report, final record, ledger event, and CLI response. `provisional` remains ineligible; no code path turns a team interpretation into organizer confirmation.

### Measured

R027 materialized the team-interpreted report, designated `final-07eadac3e123` from the exact converged EXP-009E checkpoint, and generated a 170,588-row feature-only Starter Kit output. Its SHA-256 is `60538bb59c96547bfb3e8f90ff56d8c0b5b2e2002c38ba708ecf5e2dfe82a672`; it matches the existing frozen-leader output. No retraining, test-label access, or test scoring occurred.

### Validation

The suite passes 67 tests, including a new test proving that `team_interpreted` is retained in the designated-final diagnosis while `provisional` still fails closed. README, Devpost draft, demo, requirements, and release checklist now distinguish internal completion from organizer confirmation and human publication/submission.

### Related

Task: T2-008. Decisions: D029, D031. Result: R027. Requirements: REQ-001, REQ-003, REQ-008, REQ-012–REQ-019.

## 2026-08-29 - EXP-018 strict-prior user-author affinity candidate

### Changed

Added a candidate-specific, personalised `(user_id, author_id)` long-view bucket to the BPR FM research lane. Training rows are sorted by time and encoded before their own label updates state. Validation and submission use only the completed training state. `autonomous-user-author-history` runs the registered EXP-018 five-seed candidate from the frozen BPR parent; the CLI also exposes the corresponding direct ranking flag.

### Measured

R026 completed with five-seed primary `0.603465`, +`0.000383` over BPR (`0.603082`). Both GAUC and nDCG@5 improved; the candidate remains below the `0.604017` frozen R023 leader, so it is retained as a component candidate rather than promoted. It changed 31,951 within-user pairwise relations across 8,030 users, produced a 170,588-row feature-only output from its frozen best checkpoint, and had zero mid-run interventions.

### Validation

The full suite passed 50 tests before the real run, including a new strict-prior/frozen-evaluation user-author test. The output has SHA-256 `1f2205d127a4e56c045275cb36c88e9aa79a3bc5e0b5b5526dab4e86009edfde`. No test labels were accessed or scored.

### Related

Task: T2-005. Decision: D030. Experiment: EXP-018. Result: R026. Requirements: REQ-003, REQ-004, REQ-009, REQ-018.
## 2026-08-29 - Starter-Kit-pinned execution contract and completed real 27K output recovery

### Decision and changed interface

The official PDF's Starter Kit section provides the exact executable evaluator, baseline, label, metrics, convergence rule, and submission schema, despite contradictory narrative pages. D029 therefore records the team’s **Interpretation - not explicit organizer wording**: continue on the versioned Starter-Kit-pinned `long_view` / GAUC / nDCG@5 contract rather than pause implementation. This is not an organizer confirmation; any corrected evaluator is a new incompatible profile that must be rerun.

Added normal CLI routes for Claude’s existing identity-gated implementation: `scale-resume-validation` and `scale-resume-submission`. Both require a frozen model, preflight data fingerprint, persisted state, and evaluator identity. The output route remains feature-only and does not score the test split.

### Measured

R025 deliberately interrupted a real 27K output run after a persisted checkpoint, leaving an uncheckpointed tail. Resumption started from row `16,000,000`, truncated and digest-verified the partial prefix, wrote all `114,832,239` rows, and atomically published a `4,957,087,059`-byte CSV. Its full SHA-256 exactly equals R020’s uninterrupted output: `c4e95a9702ffc61dbbf5e2a369d3902df7945d40efb033a4c9ad2caaac37fcc5`. No `.partial` artifact remained.

### Validation and status

CLI help was exercised and the full suite passes: 65 tests. T2-006 now meets its implementation definition of done and is in review pending integration; it makes no hidden-test or official bonus-score claim.

### Related

Task: T2-006. Decisions: D028, D029. Experiment: EXP-017. Results: R024, R025. Requirements: REQ-006, REQ-008, REQ-012, REQ-014, REQ-018.

## 2026-08-28 - Resumable, identity-gated 27K scale processing

### Changed

Long KuaiRand-27K passes are now recoverable. `score_scale_validation_resumable` and `generate_scale_submission_resumable` checkpoint progress beside their artifact and resume from the last boundary, but only when the frozen model SHA-256, caller-supplied data fingerprint, organizer evaluator SHA-256, canonical configuration hash, resolved output target, split, variant, and a structural signature of the source logs all still match. Any difference raises `ScaleResumeMismatch` naming the differing fields rather than resuming.

Output resumption truncates the sibling `.partial` file to the last recorded byte boundary and verifies the recorded digest before appending, so bytes from a torn write are discarded instead of being blended into the artifact. Atomic publication is unchanged: the final path is still replaced only after the last row. The cross-shard aggregation was extracted into one `_ShardAccumulator` shared by the existing and resumable validation paths, so the documented weighting has a single implementation.

### Measured

Resumed a real interrupted 27K validation. The frozen R020 model was interrupted at 30,000,000 of 71,149,570 rows, then resumed to GAUC `0.574100`, nDCG@5 `0.599412`, primary `0.586756` - identical to the uninterrupted R018/R020 figures, and produced by a different code path. A wrong data fingerprint was refused on the same real run. See R024.

### Validation

65 tests pass (49 before, 16 added). New coverage: interruption-to-resume equivalence for output generation and for both validation stages, discarding bytes written after the last checkpoint, reuse of a completed record without re-reading data, `resume=False` restart, agreement with the unsharded organizer evaluator, spy assertions that neither entry point requests the `test` split with labels, and six mismatch-rejection paths asserting the exact differing-field set.

### Known limitations

Resumed **output** generation at 27K scale is **Not yet demonstrated** on the real artifact; only validation was run end to end. The structural source signature is name/size/mtime, not a content hash over 46 GB, so the strong data identity stays the preflight fingerprint. This is provisional-contract evidence, not an organizer 27K comparison.

### Files

`src/tiktok_ml_agent/scale_baseline.py`, `tests/test_scale_baseline.py`, `docs/DECISIONS.md`, `docs/EXPERIMENTS.md`, `results_log.md`, `changelog.md`.

### Related

Task: T2-006. Decision: D028 (extends D027, D022). Experiment: EXP-017. Result: R024. Requirements: REQ-006, REQ-012, REQ-018.

### Handoff Notes

Two things for the next owner.

First, a resource-accounting caveat found while measuring: `wall_seconds` in every scale result is `time.perf_counter`, which resolves to `mach_absolute_time()` on macOS and does not advance while the system sleeps. The resumed run reported `241.64` active seconds against `11,064.5` elapsed seconds because the machine slept mid-run. R018's `526.90` and R020's `523.55` carry the same definition. Since resource use is a judged deliverable, decide deliberately whether reported timings should be active-process or elapsed time, and label them accordingly. Nothing was renamed here: the same pattern lives in modules outside this task's file scope.

Second, `docs/WORKBOARD.md` lists T2-006 as Codex-owned while `CLAUDE.md` assigns scale adaptations to Claude. This branch proceeded on explicit human instruction, which outranks the workboard under the `AGENTS.md` precedence order, and the workboard was left untouched because it is outside this task's file scope. The owning task should reconcile the row.

Committed on `divija-T2-006-scale-resume`; not pushed and not merged.

## 2026-08-28 - Release-facing documentation refresh and provenance declaration

### Changed

Updated the README, Devpost draft, demo, plan, and requirement status to match measured 27K and provisional-campaign evidence. Added a concise provenance declaration covering the permitted organizer artifacts, frozen evaluator/model identities, and no-external-data/weights policy. The unresolved organizer contract and human release actions remain explicit.

## 2026-08-28 - Ready-to-send organizer clarification draft

### Changed

Added and refined a concise email draft that asks only for the authoritative benchmark/metric, 1K/27K bonus reference, convergence definition, and official submission process. The existing rules already settle the hidden-test boundary; the Starter Kit can remain excluded from the public repository, avoiding a redistribution question. It is not sent automatically; the human team must send it and record the response under REQ-014.

## 2026-08-28 - Atomic publication for checkpoint-backed outputs

### Changed

Pure and scale submission writers now stream to sibling `.partial` files and atomically publish only after completion. An interrupted stream cannot overwrite or masquerade as the final requested artifact.

### Validation

The scale output test confirms successful publication leaves no partial file. The revalidated Pure campaign checkpoint also regenerated its real output through this path with no partial file and the same SHA-256 `60538bb…`. Full suite: 49 passing.

## 2026-08-28 - Converged provisional Pure campaign with data-identity repair

### Measured

R023 first rejected a draft campaign because historical EXP-009A and its first confirmations carried different data fingerprints. After enforcing a one-data-identity gate, EXP-009E revalidated the exact frozen leader vector and EXP-009F–H supplied three sequential declared confirmations. The repaired campaign converged under provisional ε=`0.002`, N=`3`, with leader primary `0.604017`, 0 LLM tokens, and 0 GPU-hours. `designate-final` correctly refused this report because REQ-014 is unresolved.

### Output

The revalidated leader checkpoint generated `170,588` feature-only Pure test rows plus header from the frozen manifest (SHA-256 `60538bb59c96547bfb3e8f90ff56d8c0b5b2e2002c38ba708ecf5e2dfe82a672`). This is a provisional artifact, not an official submitted final.

## 2026-08-28 - Provisional campaign gate and frozen-leader confirmations

### Changed

Campaign reports now carry an explicit confirmed/provisional contract status, and `designate-final` rejects provisional reports. Added a three-batch post-leader confirmation route (EXP-009B–D): each batch scores one predeclared frozen BPR/history/temporal rank vector and verifies its component hashes match EXP-009A before any validation work.

### Validation

Added a test proving a converged provisional report cannot create a final record. Existing campaign and full-suite checks pass (48 tests). The actual confirmation run and provisional campaign report are pending.

## 2026-08-28 - Enforced candidate deadline and timeout recovery

### Changed

The controller now enforces each planner-provided compute budget with a main-thread POSIX wall-clock deadline. A timed-out candidate is finalized as recovered, with its recovery path and budget retained in the immutable record; later siblings can continue. Threaded/non-POSIX execution deliberately keeps accounting/recovery but does not install an unsafe process-global timer.

### Validation

Qualification now records a controlled timeout recovery alongside its existing generic failure. Unit coverage proves both exhausted-budget non-execution and interruption of a running candidate. Full suite: 47 passing.

## 2026-08-28 - EXP-016 video×tab candidate-history result

### Measured

R022 completed five validation-only BPR seeds at mean primary `0.602934`, `-0.000148` versus the BPR parent. The strict-prior global video×tab bucket changed 22,725 within-user pairwise relations across 6,576 eligible validation users, but did not improve the multi-seed result. The best frozen checkpoint produced a 170,588-row, feature-only provisional output with verified alignment; no test labels were read or scored.

## 2026-08-28 - Strict-prior video×tab candidate-history lane

### Changed

Added EXP-016 as an independent BPR FM candidate. The new global video×tab long-view bucket is constructed strictly before each train event and then frozen after training for validation and feature-only submission. It is motivated by R018's scale result, not treated as a proxy or pre-accepted improvement.

### Validation

Added a synthetic strict-prior/frozen-evaluation test. The full suite has 45 passing tests. Five-seed validation is next; no result is claimed yet.

## 2026-08-28 - Frozen 27K item×tab blend selection

### Measured

R021 evaluated all declared frozen item weights `{0.25, 0.50, 0.75}`. The already-checkpointed/output-backed 0.50 setting wins at primary `0.586756`; both alternatives regress. The selection grid and validation-feedback caveat are preserved.

## 2026-08-28 - Frozen scale blend rescoring

### Changed

Added `scale-rescore`, a validation-only route that loads a frozen item×tab counter checkpoint and varies only its declared blend weight. It never re-fits tables or exposes test labels; a controlled fixture verifies the override path.

## 2026-08-28 - Full checkpointed 27K output

### Measured

R020 reran the 27K item×tab leader with a persisted 256 MB counter checkpoint, exactly reproduced its validation metrics, and streamed a 4.6 GB provisional-schema output for all 114,832,239 test rows. Header, row count, terminal row ID, and output hash were verified. No test labels were read or scored.

## 2026-08-28 - Frozen scale-model output path

### Changed

Scale baselines can now persist their bounded hashed counter tables as `.npz` checkpoints and generate a streaming `row_id,user_id,video_id,score` output solely from that checkpoint. The first R018 run predates this safeguard and is not eligible as a final scale output; any designated scale result must be rerun with a model artifact.

### Validation

Added a controlled test for save/load equivalence and feature-only submission generation. Full suite: 43 passing.

## 2026-08-28 - Cross-variant item×tab robustness

### Measured

The exact R018 item×tab mechanism improved 1K validation primary from `0.543898` to `0.545843` (+`0.001946`). R019 records it as a cross-variant robustness observation, not a 1K proxy gate or organizer-threshold claim.

## 2026-08-28 - KuaiRand-27K item×tab validation improvement

### Measured

EXP-015 completed all 71,149,570 validation rows with primary `0.586756`, +`0.029223` over R017's item-only baseline. The visible-tab cross improved nDCG@5 by `0.055259`. R018 records the full provisional-evaluator caveat; the result is not a hidden-test or official bonus-threshold claim.

## 2026-08-28 - Bounded item×tab scale candidate

### Changed

Added EXP-015, a fixed-memory blend of hashed item and item×inference-known-tab long-view rates. It uses only training labels, keeps the 27K bounded user-sharded evaluator, and can score the same item differently by visible tab. Unit coverage confirms the tab context changes the blended score on a controlled fixture.

## 2026-08-28 - KuaiRand-27K bounded streaming baseline

### Measured

EXP-011 completed full 27K train/validation streaming with a fixed 24-bit hashed popularity table and 256 user-consistent validation shards. R017 records provisional primary `0.557534` over 71,149,570 validation rows in 431.83 seconds. The result is a bonus-scale baseline, not a claim of beating an organizer benchmark.

## 2026-08-28 - Persistent scale-baseline metric artifacts

### Changed

Added `--output` to `scale-popularity`, which writes its measured JSON metrics atomically after the full bounded validation run. A first 27K invocation completed but its terminal-only JSON was unavailable after the runner's time limit; it is deliberately not recorded as a result. The repeat run will persist the evidence artifact.

## 2026-08-28 - KuaiRand-27K official artifact preflight

### Measured

Verified the official 27K archive MD5 and streamed its four standard-log shards once. R016 records 136,296,576 train, 71,149,570 validation, and 114,832,239 feature-only test rows. This proves artifact availability and split integrity, not a model score; the bounded validation baseline is now running.

## 2026-08-28 - Top-five-aware Lambda-BPR result

### Measured

EXP-014 reached mean validation primary `0.601647`, `-0.001434` versus BPR. Its top-five swap weighting changed real within-user orders but harmed both GAUC and nDCG@5. R015 retains it as a loss-family negative result; it is not a parent or ensemble component.

## 2026-08-28 - Top-five-aware Lambda-BPR candidate

### Changed

Implemented EXP-014. Lambda-BPR computes detached complete-user predicted ranks and weights pair losses by their potential nDCG@5 swap gain, mixed equally with standard BPR. It preserves same-user pair sampling, validation-only evaluation, frozen checkpoints, and the parent-ordering audit.

### Validation

Added a unit test that confirms top-five-changing swaps receive non-zero Lambda weights while swaps fully below rank five do not. Full-suite measurement is pending only because the 27K preflight is actively using local I/O.

## 2026-08-28 - Submission-facing draft and release controls

### Changed

Added a fact-checked Devpost draft and human-gated release checklist. The draft calls out the provisional metric contract, validation-only scope, current measured leader, negative results, resource accounting, and remaining 27K/final-campaign work; it does not fabricate a submission or hidden-test score.

## 2026-08-28 - Checkpoint-only final designation

### Changed

Added `designate-final`: it requires a converged campaign report, verifies the report/source evaluator/checkpoint identities, creates an immutable `designated_final` record, and preserves campaign resource totals in its diagnosis. It never retrains a model or enters a test-scoring path.

### Validation

The campaign evidence fixture now exercises full convergence → final designation and verifies the final record points to the selected source checkpoint. The suite has 40 passing tests. No real final has been designated because the current historical research ledgers are not yet a valid final campaign and REQ-014 remains unresolved.

## 2026-08-28 - Explicit campaign convergence evidence

### Changed

Added a campaign-status command that materializes epsilon/N convergence, selected batch results, evaluator identity, and resource totals from an explicit cross-ledger JSON manifest. It rejects duplicate references, failed/non-research records, mixed evaluator hashes, and any declared continuation after convergence.

### Validation

Two new campaign-evidence tests cover valid convergence/resource aggregation and mixed-evaluator rejection. The full suite has 40 passing tests. Historical research ledgers are intentionally not yet presented as a converged final campaign because their parent lineage predates this stronger campaign contract.

## 2026-08-28 - Single-pass scale preflight

### Changed

The 1K/27K preflight now counts and fingerprints all time splits in one stream instead of rescanning every log per split. Normal official date-named files are routed directly to the relevant split, reducing 27K baseline I/O while retaining a fallback for unexpected names. Test `long_view` is still not indexed or materialized. The output labels the new `one-pass-source-order-v2` fingerprint algorithm: it has identical split counts to the prior split-grouped artifact but a distinct, non-comparable digest order.

## 2026-08-28 - Denser BPR negative-sampling result

### Measured

EXP-013 reached mean validation primary `0.602820`, `-0.000262` versus BPR. The changed ordering audit and full resource record are retained in R014; the configuration is rejected as a parent.

## 2026-08-28 - Denser BPR negative-sampling candidate

### Changed

Implemented EXP-013 as a controlled sampling experiment: retain BPR, fields, splits, and seeds but draw three strictly same-user negatives per positive instead of one. The candidate has a frozen BPR parent, automatic within-user ordering audit, normal ledger evidence, and a five-seed protocol.

### Validation

Unit coverage verifies triple-negative sampling cardinality and the full suite passes before measurement. No performance result is claimed until the autonomous run completes.

## 2026-08-28 - Watch-completion auxiliary result

### Measured

EXP-007 reached mean validation primary `0.603023`, a `-0.000059` regression from BPR. The candidate changed 44,299 within-user pairwise relations across 9,088 users, so it was a genuine ranking change but not an improvement. R013 preserves the negative result and its zero-GPU, zero-token, zero-intervention evidence.

## 2026-08-28 - Train-only watch-completion candidate

### Changed

Implemented EXP-007: a BPR FM with one clipped play-time/duration completion auxiliary head. `play_time_ms` can now be loaded only for training rows; validation and test requests fail closed. The evaluated prediction remains the primary BPR long-view score. The route creates normal frozen checkpoint/manifests and supports output reconstruction.

### Validation

The new head-gradient test and validation/test access-control test pass. Full suite: 37 passing. Five-seed experiment measurement is pending; no performance claim is made.

## 2026-08-28 - Bounded KuaiRand-27K baseline route

### Changed

Replaced the scale baseline's assumption that all items and validation predictions fit in memory. KuaiRand-27K now defaults to a fixed 24-bit stable-hash popularity table and user-consistent validation shards. Every shard delegates metric calculation to the supplied evaluator; the cross-shard aggregation is explicitly matched to its documented GAUC and nDCG weighting.

### Validation

Added unit coverage for deterministic bounded hashing and shard aggregation. The full 1K baseline reproduced its previous metrics exactly through the sharded route: primary `0.543898`, GAUC `0.542570`, nDCG@5 `0.545226` (18.88 seconds, 32 shards). Full test suite: 36 passing. The 27K archive download is in progress; no 27K score is claimed yet.

## 2026-08-28 - KuaiRand-1K official bonus baseline

### Changed and measured

Downloaded KuaiRand-1K from the official Zenodo source with published-MD5 verification. Implemented and ran streaming preflight plus a train-only smoothed item-popularity baseline on the full 1K train/validation time ranges. R012 records primary `0.543898` and a 16.54-second run. Test labels were never exposed.

## 2026-08-28 - DeepFM backbone measured

### Measured

EXP-012 reached mean validation primary `0.603115`, essentially flat versus BPR and below R010. The 64-unit DeepFM configuration is retained as a negative result; its higher variance is recorded in R011.

## 2026-08-28 - DeepFM backbone lane

### Changed

Added a compact DeepFM-style BPR implementation (shared field embeddings, FM terms, nonlinear tower), its checkpoint/output support, and an autonomous five-seed EXP-012 route. The architecture uses the existing safe adapter and does not access test labels.

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
