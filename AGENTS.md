# TikTok TechJam 2026 - Track 2

## Project state

**Current phase: Phase 0 - Repository/bootstrap only.** This is a two-person hackathon project. Do not begin solution planning, architecture selection, experiments, implementation, or optimization until the human explicitly advances the project out of Phase 0.

Work on Track 2 only. The official competition PDF is authoritative.

## Authority and conflicts

Use this precedence: (1) official Track 2 PDF; (2) explicit human instruction; (3) code and tests; (4) `docs/DECISIONS.md`; (5) `docs/ARCHITECTURE.md`; (6) `docs/PLAN.md`; (7) `changelog.md`; (8) `results_log.md`; (9) other docs; (10) AI assumptions. Never silently override a higher source; flag conflicts and label inferences **Interpretation - not explicit organizer wording**.

## Required reading

Before substantial work read: `AGENTS.md`, `docs/PROBLEM.md`, `docs/REQUIREMENTS.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/PLAN.md`, recent `changelog.md`, and relevant `results_log.md`. For experiments also read `docs/EXPERIMENTS.md`.

## Operating rules

Before editing, understand the task/requirements, inspect affected code, identify expected behaviour and validation. Make the smallest coherent change; avoid unrelated refactors, premature abstraction, and speculative stack choices; preserve working behaviour unless asked otherwise; expose assumptions; prefer reproducible scripts; and never commit secrets.

After editing, run relevant checks, inspect failures, update docs and `changelog.md`, and record measured outcomes in `results_log.md`. State what was and was not validated. Never fabricate benchmarks/tests, hide failed experiments, weaken tests to pass, silently change architecture, or claim performance/correctness without evidence. If incomplete, say **Not yet demonstrated**.

For meaningful implementation: identify task and requirements; inspect code; define expected behaviour and measurement; implement; test; document. Architecture changes require an explanation plus updates to decisions, architecture, and changelog.

## Records and collaboration

Use stable, never-recycled IDs: `REQ-XXX`, `T2-XXX`, `DXXX`, `EXP-XXX`, and `RXXX`. Cancelled work keeps its ID. `changelog.md` is newest-first handoff context; `results_log.md` preserves all empirical outcomes, including failures.

`main` is integrated state; avoid direct feature development there. Use one coherent task per branch (e.g. `arjun/<task>` or `teammate/<task>`). Flow: task -> branch -> implementation -> validation -> documentation/logs -> push -> PR -> review -> merge. The branch owner remains accountable for correctness, testing, security, performance claims, and PR quality.
