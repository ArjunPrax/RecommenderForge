# Project Plan

Current Phase: **Phase 1 - Implementation**

The human advanced the project from Phase 0 on 2026-08-27. This plan implements the agreed autonomous research-agent architecture. The organizers confirmed the Starter Kit benchmark contract on 2026-08-31; final submission and public delivery remain external actions.

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

Owner: Project
Status: DONE
Priority: Critical
Depends on: T2-001

Goal: Establish versioned benchmark contracts, hidden-test protection, an append-only ledger, checkpoint identity, deterministic recovery/convergence, and the qualification-run kernel.

Relevant requirements: REQ-001, REQ-003, REQ-005, REQ-006, REQ-009, REQ-013, REQ-017, REQ-018, REQ-019

Definition of done: A deterministic qualification workflow can create isolated candidate records, fail closed on test scoring, persist a checkpoint manifest, recover a controlled failure, calculate convergence, and export a report.

Validation: Unit tests for contracts, test-access guard, evaluator delegation, ledger, convergence, recovery, checkpoint identity, and report export.

Files/components: `src/tiktok_ml_agent/`, `tests/`, root/documentation contracts.

### T2-003 - Baseline reproduction and PyTorch parity

Owner: Project
Status: DONE
Priority: Critical
Depends on: T2-002 model/benchmark interfaces and local data

Goal: Reproduce organizer references and establish a faithful pointwise PyTorch control before ranking-loss experiments.

Relevant requirements: REQ-002, REQ-003, REQ-008, REQ-018

Definition of done: Actual five-seed NumPy results are recorded; PyTorch fixed-weight parity passes; five-seed mean is within 0.001 of NumPy with no consistently directional defect.

Validation: Reproduction commands, fixed fixtures, five-seed log, sign/difference checks.

### T2-004 - Autonomous qualification run

Owner: Project
Status: DONE
Priority: Critical
Depends on: T2-002

Goal: Prove a complete non-final research loop with evidence retrieval, sibling candidates, recovery, convergence rehearsal, frozen checkpoint, validated output, and generated report.

Relevant requirements: REQ-001, REQ-005, REQ-006, REQ-009, REQ-012, REQ-013, REQ-019

Definition of done: One command completes the qualification flow and generates judge-facing evidence without hidden-test scoring.

Validation: Deterministic fixture, injected failure, resource/intervention records, report and checkpoint-manifest assertions.

### T2-005 - Autonomous ranking-objective research

Owner: Project
Status: DONE
Priority: High
Depends on: T2-003, T2-004

Goal: Run, audit, and converge ranking research as explicit candidate batches through the autonomous system.

Relevant requirements: REQ-004, REQ-005, REQ-009

Definition of done: Measured multi-seed results, mechanism-aware reflections, and an explicit campaign-level convergence/resource report are recorded.

Notes: R003–R023 and R026 executed the registered loss, history, auxiliary, temporal, backbone, sampling, and frozen-ensemble directions with preserved regressions. R035 confirms the same converged validation campaign and checkpoint-backed output under the organizer-confirmed contract.

### T2-006 - KuaiRand-1K and 27K adaptation

Owner: Project
Status: DONE
Priority: High
Depends on: organizer artifact contract, T2-004, T2-005

Goal: Stream the bonus datasets without compromising evidence, safety, or recovery.

Relevant requirements: REQ-004, REQ-008, REQ-012, REQ-013

Definition of done: Official artifacts available; baseline, scalable training, recovery, and output validation complete.

Notes: KuaiRand-1K and KuaiRand-27K official archives are checksum-verified. R012/R019/R036 record the 1K baseline, item×tab validation result, frozen model, and checkpoint-backed feature-only output. R016–R021 record 27K preflight, bounded baseline, item×tab improvement, frozen rescore, and checkpoint-backed feature-only output. R024–R025 demonstrate full 27K validation and output interruption/resume equivalence, including real torn-write truncation and matching full-output SHA-256. Pure's Starter Kit contract is organizer-confirmed; bonus-scale results remain validation/output evidence because no official bonus reference, threshold, or upload route has been supplied.

### T2-009 - Isolated child-process timeout recovery

Owner: Project
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

Owner: Project
Status: DONE
Priority: High
Depends on: T2-001

Goal: Prevent accidental publication of separately supplied organizer Starter Kit code before redistribution terms are verified.

Relevant requirements: REQ-007, REQ-011

Definition of done: The entire local Starter Kit directory is ignored, setup says how to obtain it without implying redistribution, and a test protects the ignore rule.

Validation: `tests.test_repository_safety.RepositorySafetyTests.test_organizer_starter_kit_is_unconditionally_ignored` and `git check-ignore -v --no-index kuairand-starter-kit/evaluate.py`.

Files/components: `.gitignore`, `README.md`, `docs/PROVENANCE.md`, `tests/test_repository_safety.py`.

Notes: R029 confirms that a source file within the local Starter Kit is ignored by the repository, not merely its dataset subdirectories. Organizer authorization remains necessary before deliberately redistributing any kit content.

### T2-011 - Release-integrity audit

Owner: Project
Status: DONE
Priority: High
Depends on: T2-010

Goal: Verify the reviewable branch contains no accidental competition assets or credential signatures and that its Git object graph has no integrity errors.

Relevant requirements: REQ-007, REQ-011

Definition of done: Tracked-file audit finds no data, generated artifacts, or credential/private-key signatures; `git fsck` completes with no corrupted objects; results are recorded without deleting any user data.

Validation: R030's commands and output.

Files/components: `results_log.md`, `changelog.md`, `docs/RELEASE_CHECKLIST.md`.

### T2-012 - Data-free CI integrity gate

Owner: Project
Status: DONE
Priority: High
Depends on: T2-010, T2-011

Goal: Ensure every pushed branch and pull request runs the locked dependency environment, the data-free integrity suite, and whitespace validation without downloading competition data.

Relevant requirements: REQ-003, REQ-006, REQ-011, REQ-017

Definition of done: A least-privilege GitHub Actions workflow triggers on push/PR, uses the lockfile, and runs the complete data-free unit suite plus `git diff --check`; a local contract test protects these commands.

Validation: `tests.test_ci_contract.ContinuousIntegrationContractTests.test_integrity_workflow_runs_the_locked_data_free_suite`; the repaired workflow passed both push and pull-request GitHub Actions runs before PR #1 merged.

Files/components: `.github/workflows/integrity.yml`, `tests/test_ci_contract.py`.

Notes: R031 validates the workflow syntax, locked environment, and local contract test. R033 records the initial missing-kit CI failure, repair, clean-clone verification, and successful remote rerun.

### T2-013 - Final rubric and delivery-contract audit

Owner: Project
Status: DONE
Priority: Critical
Depends on: T2-012

Goal: Reconcile the official Track 2 PDF, Starter Kit, Devpost requirements, rubric evidence, final artifact provenance, and redistribution scope before the release branch is published.

Relevant requirements: REQ-001–REQ-020

Definition of done: A written audit identifies every required external deliverable, preserves the metric-contract conflict, confirms the non-redistribution release scope, and distinguishes demonstrated evidence from pending external actions.

Validation: R032 and `docs/DELIVERY_AUDIT.md`.

Files/components: `docs/DELIVERY_AUDIT.md`, `docs/RELEASE_CHECKLIST.md`, `docs/DEMO.md`, `docs/DEVPOST_DRAFT.md`, `docs/PROVENANCE.md`, `docs/ORGANIZER_CLARIFICATION_EMAIL.md`.

### T2-014 - Public-checkout CI contract repair

Owner: Project
Status: DONE
Priority: Critical
Depends on: T2-010, T2-012, T2-013

Goal: Make the GitHub integrity workflow genuinely runnable from the public repository scope, while retaining local organizer-parity coverage when the separately obtained kit is installed.

Relevant requirements: REQ-003, REQ-006, REQ-011, REQ-017

Definition of done: The public-checkout suite passes in GitHub Actions; local environments with the kit still execute the parity tests rather than silently skipping them.

Validation: R033; a clean tracked-only Git clone; two repaired PR Actions checks passed before PR #1 merged.

Files/components: `.github/workflows/integrity.yml`, `tests/test_ci_contract.py`, `tests/test_scale_baseline.py`, `tests/test_torch_fm.py`, release records.

### T2-015 - Public README and local-instruction hygiene

Owner: Project
Status: DONE
Priority: High
Depends on: T2-013, T2-014

Goal: Present the measured implementation and limitations clearly in the public README while keeping local agent instruction files out of the repository.

Relevant requirements: REQ-010, REQ-011, REQ-012, REQ-013, REQ-019

Definition of done: README includes architecture, measured result tables, reproducible setup, safety boundaries, delivery caveats, and links to full evidence; local instruction files are ignored and no longer tracked.

Validation: Markdown link/content checks, repository-safety test, full data-free suite, and `git diff --check`.

Files/components: `README.md`, `.gitignore`, tracked documentation, local instruction files, release records.

### T2-016 - Apply organizer-confirmed benchmark contract

Owner: Project
Status: DONE
Priority: Critical
Depends on: T2-005, T2-013

Goal: Replace the resolved metric ambiguity with the organizers' confirmed Starter Kit definition and materialize an organizer-confirmed final record without changing the measured model.

Relevant requirements: REQ-002, REQ-008, REQ-012–REQ-018

Definition of done: Confirmation is recorded; current benchmark/profile documentation and future-run source notes are updated; a confirmed campaign, designated final, and feature-only output bind the same existing validation evidence and frozen checkpoint.

Validation: R035; confirmed campaign report/ledger/output; output SHA-256 equality with the historical feature-only artifact; full test suite and static checks.

Files/components: `docs/ORGANIZER_CONFIRMATION.md`, `experiments/kuairand-pure-confirmed-campaign.json`, benchmark profiles, release documentation, and evidence records.

### T2-017 - Materialize KuaiRand-1K frozen output

Owner: Project
Status: DONE
Priority: High
Depends on: T2-006, organizer bonus submission route

Goal: Bind the previously measured 1K item×tab scale candidate to a frozen bounded model and generate an aligned feature-only output, while preserving the unconfirmed bonus-scoring scope.

Relevant requirements: REQ-003, REQ-008, REQ-012, REQ-017

Definition of done: The model is rebuilt from training labels only; its validation result matches R019; the feature-only CSV is sequential, finite, and checksum-recorded; public materials do not claim an organizer 1K/27K threshold or submission process.

Validation: R036; 72-test suite; output header/row-ID/finiteness audit; `uv lock --check`; Markdown link check; `git diff --check`.

Files/components: scale output artifacts (ignored), `results_log.md`, scale profile wording, release/Devpost/README documentation.
