# Architecture

Status: **Accepted for Phase 1 implementation**

## System overview

The project is an autonomous research control plane around organizer-supplied recommender benchmarks. It plans a bounded candidate batch from immutable parents, executes candidates in isolated worktrees, delegates validation to a versioned organizer evaluator, stores immutable evidence, reflects on the outcome, and selects the next parent or converges.

## Components

- **Benchmark contract and adapter:** data partitions, evaluator path/hash, submission schema, hidden-test policy.
- **Scale adapter:** streams official 1K/27K logs, uses bounded item statistics and user-consistent validation shards, and never exposes bonus-test labels.
- **Train-only auxiliary channel:** can expose organizer outcomes such as watch completion only to a training candidate; validation/test records cannot carry those fields.
- **Research knowledge base:** structured evidence cards for papers, organizer guidance, and measured findings.
- **Memory manager:** bounded planner context distilled from, but never replacing, the append-only ledger.
- **Planner:** produces 1–3 ranked `ExperimentSpec` siblings with evidence and one primary operator family.
- **Executor:** invokes a host-owned command factory in a disposable candidate worktree; candidate patches are path-scoped and must emit structured result JSON.
- **Validator:** static checks, test-access policy, checkpoint checks, and organizer evaluator delegation.
- **Ledger:** SQLite/JSON evidence with run class, hypothesis, diff/config/data/evaluator identity, metrics, reflection, failures, and resources.
- **Controller:** deterministic candidate selection, recovery, convergence, checkpoint freezing, and report export.
- **Campaign convergence:** evaluates epsilon/N over complete candidate batches across the campaign, rather than incorrectly treating siblings as sequential iterations.

## Data flow

```text
BenchmarkSpec + KnowledgeBase + MemorySnapshot
                  -> Planner -> CandidateBatch
                  -> isolated candidate execution
                  -> validator + organizer evaluator
                  -> RunRecord + artifacts
                  -> reflection + memory consolidation
                  -> promote / recover / converge / checkpoint-backed output
```

## Interfaces

- `BenchmarkSpec`: dataset/splits/label/evaluator hash/baseline/convergence/schema/policy.
- `ExperimentSpec`: stable ID, run class, parent, hypothesis, source evidence, operator, config, controls, budgets.
- `RunRecord`: append-only measured outcome and lifecycle state.
- `CheckpointManifest`: content hashes binding the measured checkpoint to code/data/evaluator/config/predictions.
- `EvidenceCard` and `MemorySnapshot`: retrievable research evidence and bounded planner state.
- `campaign-status`: materializes an auditable convergence/resource report from explicit cross-ledger run references; it refuses mixed evaluators and post-convergence continuation.

## Execution environment

Python is managed through a project-local `uv` environment after compatibility verification. The NumPy baseline remains runnable without PyTorch. PyTorch is admitted only after fixed-weight and five-seed pointwise parity.

## Trust/security boundaries

- Candidate code cannot retrieve test labels or locally score test data.
- Candidates cannot select shell commands; only a host-owned command factory executes after static diff validation.
- The adapter delegates to the organizer evaluator, whose hash is recorded.
- Every accepted prediction is traceable to an immutable checkpoint manifest.
- Data, generated artifacts, caches, submissions, and secrets are git-ignored.

## Observability

Run records include timings, CPU/MPS/CUDA use, peak memory, LLM tokens, attempt count, failure/recovery history, interventions, and event timestamps. Generated reports aggregate qualification, research, and designated-final runs separately.

## Evaluation path

Use the organizer evaluator for any official validation score. Inner development is available for model-internal training controls but is not a candidate-rejection proxy unless correlation has been demonstrated. Final claims use the declared multi-seed protocol.

## Known tradeoffs

- The starter evaluator is provisional due to the organizer conflict.
- Bounded operator taxonomy improves safety and comparability, but `novel` preserves exploration.
- Working-memory summaries reduce token growth; the original ledger remains retrievable.
- Full-fidelity Pure evaluation is preferred over unvalidated small-data pruning.
