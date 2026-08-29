# Project Plan

Current Phase: **Phase 1 - Implementation**

The human advanced the project from Phase 0 on 2026-08-27. This plan implements the agreed autonomous research-agent architecture. Organizer metric/label ambiguity remains a tracked blocker for final benchmark designation, not for the platform foundation.

1. Phase 0 - Repository and collaboration bootstrap
2. Phase 1 - Problem analysis and research
3. Phase 2 - Solution candidates and technical feasibility
4. Phase 3 - Baselines and evaluation harness
5. Phase 4 - MVP implementation
6. Phase 5 - Optimization / experimentation
7. Phase 6 - Integration
8. Phase 7 - Demo and judging preparation
9. Phase 8 - Final validation / submission

## Task format

### T2-XXX - Task name

Owner:
Status: BACKLOG
Priority:
Depends on:

Goal:

Relevant requirements:

Definition of done:

Validation:

Files/components:

Notes:

Use `BACKLOG`, `READY`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, or `DONE`. Never recycle IDs.

## Phase 0

### T2-001 - Establish repository and collaboration bootstrap

Owner: Human team
Status: DONE
Priority: High
Depends on: None

Goal: Create/push private bootstrap repository and Track 2-only context.

Relevant requirements: REQ-009, REQ-011, REQ-014

Definition of done: Structure validated; private remote created; bootstrap committed/pushed; PDF conflict recorded. Teammate access remains a user-managed follow-up.

Validation: Inspect structure, remote privacy, commit, push.

Files/components: Root docs, `docs/`, `.github/`.

Notes: Bootstrap is committed and pushed. The human advanced the project on 2026-08-27.

## Phase 1

### T2-002 - Platform foundation and benchmark integrity

Owner: Codex
Status: DONE
Priority: Critical
Depends on: T2-001

Goal: Establish versioned benchmark contracts, hidden-test protection, an append-only ledger, checkpoint identity, deterministic recovery/convergence, and the qualification-run kernel.

Relevant requirements: REQ-001, REQ-003, REQ-005, REQ-006, REQ-009, REQ-013, REQ-017, REQ-018, REQ-019

Definition of done: A deterministic qualification workflow can create isolated candidate records, fail closed on test scoring, persist a checkpoint manifest, recover a controlled failure, calculate convergence, and export a report.

Validation: Unit tests for contracts, test-access guard, evaluator delegation, ledger, convergence, recovery, checkpoint identity, and report export.

Files/components: `src/tiktok_ml_agent/`, `tests/`, root/documentation contracts.

### T2-003 - Baseline reproduction and PyTorch parity

Owner: Codex
Status: DONE
Priority: Critical
Depends on: T2-002 model/benchmark interfaces and local data

Goal: Reproduce organizer references and establish a faithful pointwise PyTorch control before ranking-loss experiments.

Relevant requirements: REQ-002, REQ-003, REQ-008, REQ-018

Definition of done: Actual five-seed NumPy results are recorded; PyTorch fixed-weight parity passes; five-seed mean is within 0.001 of NumPy with no consistently directional defect.

Validation: Reproduction commands, fixed fixtures, five-seed log, sign/difference checks.

### T2-004 - Autonomous qualification run

Owner: Codex
Status: DONE
Priority: Critical
Depends on: T2-002

Goal: Prove a complete non-final research loop with evidence retrieval, sibling candidates, recovery, convergence rehearsal, frozen checkpoint, validated output, and generated report.

Relevant requirements: REQ-001, REQ-005, REQ-006, REQ-009, REQ-012, REQ-013, REQ-019

Definition of done: One command completes the qualification flow and generates judge-facing evidence without hidden-test scoring.

Validation: Deterministic fixture, injected failure, resource/intervention records, report and checkpoint-manifest assertions.

### T2-005 - Autonomous ranking-objective research

Owner: Claude
Status: DONE
Priority: High
Depends on: T2-003, T2-004

Goal: Run, audit, and converge ranking research as explicit candidate batches through the autonomous system.

Relevant requirements: REQ-004, REQ-005, REQ-009

Definition of done: Measured multi-seed results, mechanism-aware reflections, and an explicit campaign-level convergence/resource report are recorded.

Notes: R003–R023 and R026 executed the registered loss, history, auxiliary, temporal, backbone, sampling, and frozen-ensemble directions with preserved regressions. R023 converged the declared five-seed campaign; R027 binds its leader to the team-interpreted checkpoint-backed output.

### T2-006 - KuaiRand-1K and 27K adaptation

Owner: Codex + Claude
Status: DONE
Priority: High
Depends on: organizer artifact contract, T2-004, T2-005

Goal: Stream the bonus datasets without compromising evidence, safety, or recovery.

Relevant requirements: REQ-004, REQ-008, REQ-012, REQ-013

Definition of done: Official artifacts available; baseline, scalable training, recovery, and output validation complete.

Notes: KuaiRand-1K and KuaiRand-27K official archives are checksum-verified. R012 records the 1K baseline; R016–R021 record 27K preflight, bounded baseline, item×tab improvement, frozen rescore, and checkpoint-backed feature-only output. R024–R025 demonstrate full 27K validation and output interruption/resume equivalence, including real torn-write truncation and matching full-output SHA-256. D029 permits continued execution under the Starter-Kit-pinned contract. The implementation is integrated; it makes no hidden-test or organizer 27K-score claim.

### T2-009 - Isolated child-process timeout recovery

Owner: Codex
Status: DONE
Priority: High
Depends on: T2-002

Goal: Prove that the controller's wall-clock budget terminates a real trusted child process and always removes its disposable Git worktree.

Relevant requirements: REQ-006, REQ-009, REQ-019

Definition of done: A POSIX integration test runs a real sleeping subprocess through the isolated worktree executor, records controlled timeout recovery, and proves no worktree remains.

Validation: `tests.test_controller.ControllerTests.test_wall_clock_timeout_kills_isolated_child_and_cleans_worktree`.

Files/components: `tests/test_controller.py`, `src/tiktok_ml_agent/controller.py`, `src/tiktok_ml_agent/worktree_executor.py`.

Notes: R028 exercises the real POSIX subprocess and Git-worktree boundaries in a disposable temporary repository. It is not a benchmark run and does not access competition data.

### T2-010 - Starter Kit publication isolation

Owner: Codex
Status: DONE
Priority: High
Depends on: T2-001

Goal: Prevent accidental publication of separately supplied organizer Starter Kit code before redistribution terms are verified.

Relevant requirements: REQ-007, REQ-011

Definition of done: The entire local Starter Kit directory is ignored, setup says how to obtain it without implying redistribution, and a test protects the ignore rule.

Validation: `tests.test_repository_safety.RepositorySafetyTests.test_organizer_starter_kit_is_unconditionally_ignored` and `git check-ignore -v --no-index kuairand-starter-kit/evaluate.py`.

Files/components: `.gitignore`, `README.md`, `docs/PROVENANCE.md`, `tests/test_repository_safety.py`.

Notes: R029 confirms that a source file within the local Starter Kit is ignored by the repository, not merely its dataset subdirectories. Organizer authorization remains necessary before deliberately redistributing any kit content.
