# Decisions

Use this lightweight ADR format for meaningful decisions.

## DXXX - Decision title

Date:
Status: Proposed / Accepted / Superseded / Rejected

### Context

### Decision

### Why

### Alternatives Considered

### Consequences

### Related

- Requirements:
- Tasks:
- Experiments:
- PRs/commits:

## D005 - Preserve organizer-source ambiguity

Date: 2026-08-26
Status: Accepted

### Context

The supplied PDF conflicts over the required primary benchmark.

### Decision

Record both claims and make no technical selection during Phase 0.

### Why

Official sources outrank AI interpretation.

### Alternatives Considered

Selecting a benchmark from only part of the PDF.

### Consequences

REQ-014 must be clarified before affected planning.

### Related

- Requirements: REQ-014
- Tasks: T2-001

## D006 - Advance to Phase 1 implementation

Date: 2026-08-27
Status: Accepted

### Context

The human explicitly authorized full implementation after reviewing the plan.

### Decision

Advance the project from bootstrap to implementation while retaining unresolved organizer ambiguity as a versioned benchmark-contract blocker.

### Why

The platform foundation, safety controls, baseline reproduction, and qualification workflow are useful under either possible KuaiRand metric profile.

### Consequences

Phase 1 tasks and code may proceed. Final metric-specific model selection remains blocked by REQ-014.

### Related

- Requirements: REQ-001, REQ-014
- Tasks: T2-002

## D007 - Provisional organizer evaluator delegation

Date: 2026-08-27
Status: Accepted

### Context

The updated PDF conflicts over KuaiRand target and metrics. The supplied starter kit includes runnable `evaluate.py` and baseline references.

### Decision

Use the starter evaluator as the provisional executable contract, recording its path and SHA-256 hash. The adapter delegates to it instead of reimplementing official metrics.

### Why

It is the only complete runnable organizer artifact, while preserving an auditable route to replace it if organizers issue a correction.

### Consequences

All results carry an evaluator hash and cannot be compared across changed evaluator versions.

### Related

- Requirements: REQ-008, REQ-014, REQ-015
- Tasks: T2-002, T2-003

## D008 - Fail closed on hidden-test access

Date: 2026-08-27
Status: Accepted

### Decision

Candidate-facing APIs reject test-label access and development test scoring. Only submission-row features/identifiers may be read for output generation.

### Why

The starter kit physically contains local test labels, while the organizer rules prohibit their use.

### Consequences

Every denied attempt is ledgered. The starter kit's local test-score route is not exposed through the agent.

### Related

- Requirements: REQ-003, REQ-017
- Tasks: T2-002

## D009 - Immutable checkpoint-backed outputs

Date: 2026-08-27
Status: Accepted

### Decision

Freeze a manifest that binds code, data, evaluator, configuration, metrics, prediction hash, and checkpoint hash. Submission output loads that checkpoint; it never retrains.

### Why

The measured validation result must describe the submitted model.

### Related

- Requirements: REQ-012, REQ-018
- Tasks: T2-002, T2-004

## D010 - Stable experiment IDs and explicit run classes

Date: 2026-08-27
Status: Accepted

### Decision

Assign stable EXP-001 through EXP-011 in `docs/EXPERIMENTS.md`. Each run is `qualification`, `research`, or `designated_final`; results are never renumbered or conflated.

### Why

It prevents identifier recycling and separates rehearsal resource/intervention accounting from the designated final run.

### Related

- Requirements: REQ-009, REQ-013, REQ-019
- Tasks: T2-002, T2-004

## D011 - Bounded runtime memory and operator taxonomy

Date: 2026-08-27
Status: Accepted

### Decision

Keep an append-only ledger, retrieve structured evidence cards at runtime, and periodically create bounded working-memory snapshots. Each experiment has one primary operator family; `novel` remains available with justification.

### Why

This controls token growth, makes research choices traceable, and prevents malformed unrestricted changes without reducing the evidence base to a human-authored script.

### Related

- Requirements: REQ-001, REQ-005, REQ-013, REQ-019
- Tasks: T2-002, T2-004

## D012 - Stable child identifiers for sibling objective candidates

Date: 2026-08-28
Status: Accepted

### Context

EXP-004 is the fixed parent research family for ranking objectives, but BPR and exact listwise loss are distinct sibling changes that must each retain their own ledger evidence.

### Decision

Use append-only child IDs `EXP-004A` (BPR) and `EXP-004B` (exact listwise) underneath EXP-004. This expands the registered family; it does not reassign EXP-005, which remains reserved for history/temporal crosses.

### Why

The ledger needs a unique immutable experiment identifier per sibling, while the plan needs to retain the original family taxonomy.

### Related

- Requirements: REQ-009, REQ-019
- Tasks: T2-005
- Experiments: EXP-004, EXP-004A, EXP-004B

## D013 - Train-only frozen validation history

Date: 2026-08-28
Status: Accepted

### Context

User-history features can leak evaluation labels, and a user-constant score cannot alter a within-user ranking by itself.

### Decision

For EXP-005, construct training history strictly before each training event and freeze validation history after the training period. Use the resulting categorical bucket only as an FM field so it can interact with candidate video, author, tab, and duration features. Never update it with validation labels.

### Why

This preserves a meaningful candidate-specific mechanism while making the temporal anti-leakage rule testable.

### Related

- Requirements: REQ-003, REQ-004, REQ-009
- Tasks: T2-005
- Experiments: EXP-005

## D014 - Frozen-component rank ensembles only

Date: 2026-08-28
Status: Accepted

### Decision

An ensemble candidate must consume immutable component checkpoints and saved validation predictions. Its blend grid, component manifests, selected weight, and five-seed results are ledgered; component models are never retrained as part of blending.

### Why

This makes a possible complementary-rank gain reproducible and prevents silently reusing test scoring or replacing a validated component.

### Related

- Requirements: REQ-003, REQ-009, REQ-018
- Experiments: EXP-009

## D015 - EXP-009 child for three-component ensemble

Date: 2026-08-28
Status: Accepted

### Decision

Use `EXP-009A` as the append-only child of EXP-009 for the BPR/history/temporal three-component candidate. EXP-009 retains its two-component result.

### Why

The candidate has distinct component manifests and a distinct declared weight grid, so it requires an independent immutable experiment identity.

## D016 - Convergence counts batches, not sibling candidates

Date: 2026-08-28
Status: Accepted

### Decision

Apply the provisional epsilon/N convergence rule to the selected result of each complete candidate batch. Sibling candidates share a parent and are alternatives within one iteration, so they must not consume multiple stagnation counts.

### Why

This preserves the intended atomicity of an autonomous proposal/execute/select loop and makes the stopping audit reproducible.

## D017 - Compact DeepFM architecture lane

Date: 2026-08-28
Status: Accepted

### Decision

Add EXP-012 as a bounded DeepFM-style BPR backbone trial: FM terms plus a 64-unit nonlinear tower over the same categorical field embeddings.

### Why

It tests a distinct higher-order interaction mechanism without changing the benchmark adapter, data policy, loss, or seed protocol.

## D018 - Explicit cross-ledger campaign evidence

Date: 2026-08-28
Status: Accepted

### Context

Research batches are stored in isolated ledgers so their artifacts cannot overwrite one another. A final convergence claim must not silently discover arbitrary historical runs or count sibling candidates as sequential iterations.

### Decision

Materialize campaign status only from a declarative JSON file that names every source ledger and eligible run. Enforce a common benchmark/evaluator identity, one use of each run, one selected result per batch, and no continuation after epsilon/N convergence. Aggregate resource totals from the referenced immutable run records.

### Why

This makes the convergence and resource claim reviewable while preserving isolated experiment ledgers.

### Related

- Requirements: REQ-005, REQ-009, REQ-013, REQ-016, REQ-019
- Tasks: T2-005

## D019 - Designate finals only from converged campaign evidence

Date: 2026-08-28
Status: Accepted

### Decision

Create a new immutable `designated_final` ledger record only when a campaign report is converged and its selected source checkpoint, evaluator hash, and report hash all verify. The operation may generate an output from that frozen checkpoint, but it never retrains or scores test labels.

### Why

This prevents a peak model or a newly retrained model from being mislabeled as the submitted converged result.

### Related

- Requirements: REQ-003, REQ-012, REQ-013, REQ-016, REQ-018
- Tasks: T2-005

## D020 - Top-five-aware Lambda-BPR objective lane

Date: 2026-08-28
Status: Accepted

### Decision

Add EXP-014 as a controlled loss-objective candidate. It mixes ordinary same-user BPR loss with a detached nDCG@5 swap-gain-weighted BPR loss; all features, pairs, split, optimizer, and seeds remain fixed.

### Why

The primary metric combines GAUC and nDCG@5. This is a direct, testable mechanism for placing additional training emphasis on pair swaps that can affect the latter, without changing data access or copying the evaluator.

### Related

- Requirements: REQ-003, REQ-004, REQ-008, REQ-009
- Experiments: EXP-014

## D021 - Bounded item×tab scale candidate

Date: 2026-08-28
Status: Accepted

### Decision

Add a fixed-memory item×inference-known-tab popularity cross for 1K/27K scale experiments. It trains separate hashed item and item×tab rate tables on training labels only, then blends their smoothed rates during validation/test feature scoring.

### Why

The item-only scale baseline cannot use a candidate's visible tab/context. The cross can change an individual user's ordering without retaining the full 27K item universe or looking at any future outcome.

### Related

- Requirements: REQ-003, REQ-004, REQ-008
- Tasks: T2-006

## D022 - Frozen scale models for feature-only outputs

Date: 2026-08-28
Status: Accepted

### Decision

Persist bounded hashed scale models after fitting and generate scale submissions only by loading that exact persisted artifact. The output streamer exposes test identifiers/features only and verifies sequential rows plus finite scores while writing.

### Why

Scale candidates must meet the same no-retrain final-output standard as Pure checkpoints. A transient terminal metric without its fitted table is not eligible for designation.

### Related

- Requirements: REQ-003, REQ-012, REQ-015, REQ-018
- Tasks: T2-006

## D023 - Frozen scale blend rescoring

Date: 2026-08-28
Status: Accepted

### Decision

Permit a declared item×tab blend-weight comparison only by re-evaluating the same frozen persisted counter tables. The rescore path cannot fit a new model or access test labels.

### Why

It isolates one hyperparameter from model/data changes and preserves checkpoint provenance for any selected scale configuration.

### Related

- Requirements: REQ-003, REQ-004, REQ-009, REQ-018
- Experiments: EXP-015

## D024 - Strict-prior video×tab candidate-history lane

Date: 2026-08-28
Status: Accepted

### Context

EXP-015's frozen 27K item×tab scale result provides a bounded, cross-variant indication that the visible candidate/tab interaction may be useful. KuaiRand-Pure's FM already receives raw video and tab fields, but it has not received an engagement-rate representation of their interaction.

### Decision

Evaluate one independent EXP-016 BPR candidate with a categorical global video×tab long-view bucket. Training rows receive the bucket computed before their own timestamp-ordered label update; validation and submission rows use the completed training-only state. This field is evaluated independently from user-history and weekday fields.

### Why

The feature varies across candidates within a user impression list, unlike a user-only first-order feature, while the strict-prior/frozen construction mechanically prevents validation or test-label leakage.

### Consequences

Five-seed validation is required before any promotion decision. EXP-016 remains a research result even if it improves validation; final metric-specific selection remains blocked by REQ-014.

### Related

- Requirements: REQ-003, REQ-004, REQ-009, REQ-018
- Tasks: T2-005
- Experiments: EXP-016, EXP-015

## D025 - Enforce planner wall-clock budgets

Date: 2026-08-28
Status: Accepted

### Context

The controller could classify a raised `TimeoutError`, but a planned compute budget did not interrupt a stalled in-process candidate. This left the runtime-recovery claim weaker than its ledger schema.

### Decision

On the main POSIX thread, wrap every candidate with its planner-supplied `compute_budget_seconds` in an interval-timer deadline. An expired or zero budget raises `TimeoutError`, is finalized as a recovered record, preserves partial artifacts, and allows sibling execution to continue. Non-POSIX or threaded hosts retain accounting/recovery but do not install a process-global signal handler.

### Why

The mechanism makes the candidate compute budget operational without introducing an unrestricted subprocess or weakening the immutable parent/recovery policy.

### Consequences

The qualification fixture records a controlled timeout recovery, and tests cover both an already-exhausted budget and interruption of an in-flight candidate. This is controller evidence; it is not a claim that an arbitrary external subprocess can be preempted.

### Related

- Requirements: REQ-006, REQ-009, REQ-013, REQ-019
- Tasks: T2-004, T2-006

## D026 - Provisional-contract finalization gate and frozen-leader confirmations

Date: 2026-08-28
Status: Accepted

### Context

The organizer PDF/Starter Kit metric conflict is unresolved (REQ-014). A converged local campaign must not be able to silently become an official designated final. At the same time, the final campaign needs post-leader evidence rather than a retrospective collection of unrelated historical runs.

### Decision

Campaign manifests now declare `contract_status` as `confirmed` or `provisional`; only confirmed reports are eligible for `designate-final`. Campaign evaluation also requires one common data fingerprint and evaluator hash. After the initial EXP-009A/EXP-009B–D draft exposed a data-fingerprint mismatch, revalidate the exact historical vector as EXP-009E, then run EXP-009F, EXP-009G, and EXP-009H as three sequential, single-vector frozen-ensemble confirmations. Before executing, verify each BPR/history/temporal component checkpoint hash exactly matches the frozen leader artifact.

### Why

This preserves a real, immutable post-leader sequence and prevents an implementation convenience from bypassing a documented organizer-contract blocker. Single predeclared vectors avoid treating repeated validation feedback as an unrestricted ensemble search.

### Consequences

The resulting campaign may demonstrate provisional convergence and resource accounting, but no official final record can be designated until REQ-014 is resolved. A full campaign ledger retains all vectors, metrics, and zero-token policy provenance.

### Related

- Requirements: REQ-003, REQ-008, REQ-012, REQ-013, REQ-014, REQ-016, REQ-018
- Tasks: T2-005
- Experiments: EXP-009A through EXP-009H

## D027 - Atomic checkpoint-backed output publication

Date: 2026-08-28
Status: Accepted

### Context

Long CSV streams can be interrupted after their final filename has already been created. A partial file at the final path could be mistaken for a valid submission.

### Decision

Pure and scale submission writers now write to a sibling `.partial` path and atomically replace the requested final path only after all rows have been written and validated. If generation fails, the old final file remains untouched and the partial artifact remains available for diagnosis.

### Why

It preserves the required frozen-checkpoint provenance while making failed long output runs distinguishable from valid artifacts.

### Related

- Requirements: REQ-006, REQ-012, REQ-015, REQ-018
- Tasks: T2-004, T2-006

## D030 - Strict-prior user-author affinity candidate lane

Date: 2026-08-29
Status: Accepted

### Context

The base BPR FM has user, video, author, tab, and duration fields, but its tested history feature has only represented global user engagement. A user-author history can vary across candidate videos within a user’s ranking list, making it a valid personalised ranking feature if it does not consume validation or test labels.

### Decision

Evaluate EXP-018 as one independent five-seed BPR candidate. Each training row receives the `(user_id, author_id)` long-view bucket from strictly earlier training events before its own label updates state. Validation and feature-only submission rows use only the completed training state. The feature is evaluated independently from all other optional history/temporal fields, and a runtime ordering audit must show that it changes within-user validation relations before its metric can be considered.

### Why

This tests a candidate-specific personal-affinity mechanism that the existing user-global and video-tab features do not represent, while preserving a mechanical, testable temporal anti-leakage boundary.

### Consequences

The result will be retained whether it improves or regresses. It cannot be promoted on a single seed; its five-seed mean is compared against R003 BPR and may become an ensemble component only after immutable checkpoint/prediction provenance is recorded.

### Related

- Requirements: REQ-003, REQ-004, REQ-009, REQ-018
- Tasks: T2-005
- Experiments: EXP-018, EXP-004A

## D004 - Retain experimental evidence

Date: 2026-08-26
Status: Accepted

### Context

Research includes failures and regressions.

### Decision

Keep all measured outcomes in `results_log.md`.

### Why

Project claims must remain evidence-driven and reproducible.

### Alternatives Considered

Deleting failed work from project knowledge.

### Consequences

Future work can learn from negative outcomes.

## D003 - Changelog is the handoff log

Date: 2026-08-26
Status: Accepted

### Context

Humans and future agents need recent context.

### Decision

Use newest-first `changelog.md` for meaningful changes and handoff notes.

### Why

The current state stays discoverable without chat history.

### Consequences

Meaningful changes require a changelog entry.

## D002 - PR-based collaboration

Date: 2026-08-26
Status: Accepted

### Context

Two developers may use branches/worktrees and AI tools.

### Decision

Use coherent task branches and PRs; reserve `main` for integration.

### Why

Review reduces coordination risk.

### Consequences

Meaningful work should be locally validated and reviewed where practical.

## D001 - Repository is the durable source of truth

Date: 2026-08-26
Status: Accepted

### Context

AI conversations are scratch space.

### Decision

Document material decisions, assumptions, experiments, results, changes, and handoffs in the repository.

### Why

Future collaborators must understand the project without chat history.

### Consequences

Documentation and logs are part of meaningful work.
