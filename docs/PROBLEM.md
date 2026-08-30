# Track 2 Problem

Source: official **Tiktok Techjam Prob Statements** PDF supplied by the user, updated 2026-08-26, pages 1-12. This describes the problem, not a solution.

## Official Problem Statement

Design and implement an **Autonomous ML Research Agent** for recommender systems. For each benchmark, the agent autonomously reproduces the official baseline, iterates using training data and public validation feedback only, and improves over the baseline. Writing and revising code is part of the agent's job.

## Context

The organizer frames MLE as a loop: read problem, inspect data, engineer features, train/tune, evaluate, then reflect/revise. Track 2 asks to automate this loop.

## Required Objective

Run the full pipeline autonomously to a converged result and aim to exceed the official baseline on hidden test. Improve based on the agent's own evaluation, minimise human intervention, and recover/retry/route around failures so long runs do not crash, stall, or diverge.

## Hard Constraints

- Development uses only fixed training split and public validation feedback; hidden test is never accessed during development.
- No external training data, augmentation/joining from other datasets, or pretrained weights trained on these benchmarks' test labels.
- Hidden test is scored once on final designated submission.
- Compute budget is **TBD**.

## Explicit Non-Goals, if specified

External training data and hidden-test access are out of scope. No technical non-goals are inferred.

## Required Deliverables

- Devpost description: solution/problem relation; development tools; APIs; libraries/frameworks; datasets/assets.
- **Public** code/GitHub repository with structured/commented code and README overview, setup, reproduction, limitations, and contributions.
- Per-iteration logs: hypothesis, code diff, metrics, error/recovery events; plus manual-intervention count.
- Final output/checkpoint in Starter Kit schema and result table with validation-best metrics and baseline delta.
- Total LLM input/output tokens and GPU-hours to convergence.

## Acceptance Requirements

Baseline reproduction, autonomous iteration, convergence, recovery/robustness, and compliant final output are required. Detailed trackable statements are in `REQUIREMENTS.md`.

## Evaluation / Judging Criteria

Technical Execution 35%; Innovation & Problem Insight 20%; Impact & Relevance 20%; Feasibility & Practicality 15%; Presentation & Communication (final event only) 10%.

The technical score uses the converged result, not the peak. Per metric, hidden-test delta is agent score minus official baseline; dataset score is mean metric delta. Autonomy is measured primarily by manual interventions. Feasibility includes LLM tokens and GPU-hours.

## Current Benchmarks

- KuaiRand-Pure is required and determines the primary score.
- KuaiRand-1K and KuaiRand-27K are organizer bonus benchmarks; the team treats both as internal must-attempt targets once official artifacts exist.
- AliCCP is absent from the updated 12-page PDF and is out of scope unless organizers explicitly reintroduce it.

## Open Questions / Ambiguities

**Organizer-source conflict - requires clarification.** The starter kit pins `long_view`, GAUC, and nDCG@5. PDF pages 4, 6, 7, and 8 instead describe `click`, nDCG@10, and Recall@50. The PDF says the Starter Kit pins the exact label/metrics, but its narrative contradicts that claim. **Interpretation - not explicit organizer wording:** D029/D031 permit a team-interpreted technical designation under the versioned Starter Kit profile; an organizer response remains required for organizer-confirmed reporting.
