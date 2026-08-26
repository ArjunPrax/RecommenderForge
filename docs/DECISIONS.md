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
