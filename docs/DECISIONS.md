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
