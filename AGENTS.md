# TikTok TechJam 2026 - Track 2

## Project state

**Current phase: Phase 1 - implementation.** The human explicitly advanced the repository on 2026-08-27. This is a two-person hackathon project implementing an autonomous ML research agent for Track 2.

Work on Track 2 only. The official competition PDF is authoritative. The downloadable organizer evaluator is the provisional executable contract until the organizer resolves the documented label/metric conflict.

## Authority and conflicts

Use this precedence: (1) official Track 2 PDF; (2) explicit human instruction; (3) code and tests; (4) `docs/DECISIONS.md`; (5) `docs/ARCHITECTURE.md`; (6) `docs/PLAN.md`; (7) `changelog.md`; (8) `results_log.md`; (9) other docs; (10) AI assumptions. Never silently override a higher source; flag conflicts and label inferences **Interpretation - not explicit organizer wording**.

## Required reading

Before substantial work read: `AGENTS.md`, `docs/PROBLEM.md`, `docs/REQUIREMENTS.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/PLAN.md`, recent `changelog.md`, and relevant `results_log.md`. For experiments also read `docs/EXPERIMENTS.md`.

## Operating rules

Before editing, understand the task/requirements, inspect affected code, identify expected behaviour and validation. Make the smallest coherent change; avoid unrelated refactors, premature abstraction, and speculative stack choices; preserve working behaviour unless asked otherwise; expose assumptions; prefer reproducible scripts; and never commit secrets.

After editing, run relevant checks, inspect failures, update docs and `changelog.md`, and record measured outcomes in `results_log.md`. State what was and was not validated. Never fabricate benchmarks/tests, hide failed experiments, weaken tests to pass, silently change architecture, or claim performance/correctness without evidence. If incomplete, say **Not yet demonstrated**.

## Benchmark integrity

- Never access, score, inspect, or use hidden-test labels during development. Candidate-facing code must fail closed when asked for test labels or test scoring.
- Delegate metric calculation to the organizer evaluator and record its path/hash. Do not silently reimplement or modify it.
- Use immutable code/configuration/data/evaluator/checkpoint identities for every accepted result. Generate final predictions from the measured checkpoint; never retrain a different final model.
- Use inner development only for training controls such as early stopping. It is not a rejection proxy unless a documented correlation experiment proves it predictive.
- Treat a single seed as screening evidence only. Final promotion/convergence claims require the declared multi-seed procedure.
- Label unresolved organizer rules **Interpretation - not explicit organizer wording** in decisions and reports.

## Autonomous-run records

Every eligible run has a stable `EXP-XXX` identifier, `run_class` (`qualification`, `research`, or `designated_final`), an operator family, hypothesis, diff hash, evidence source, metrics, resource usage, failure/recovery information, and a mechanism-aware reflection. The append-only ledger is the source of truth; summaries may never replace it.

For meaningful implementation: identify task and requirements; inspect code; define expected behaviour and measurement; implement; test; document. Architecture changes require an explanation plus updates to decisions, architecture, and changelog.

## Records and collaboration

Use stable, never-recycled IDs: `REQ-XXX`, `T2-XXX`, `DXXX`, `EXP-XXX`, and `RXXX`. Cancelled work keeps its ID. `changelog.md` is newest-first handoff context; `results_log.md` preserves all empirical outcomes, including failures.

`main` is integrated state; avoid direct feature development there. Use one coherent task per branch. Because the existing `Arjun` branch occupies the `arjun` namespace, use `arjun-T2-XXX-short-name` and `divija-T2-XXX-short-name`. Flow: task -> branch -> implementation -> validation -> documentation/logs -> push -> PR -> review -> merge. The branch owner remains accountable for correctness, testing, security, performance claims, and PR quality.
