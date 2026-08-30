# Final Delivery and Rubric Audit

Audit date: 2026-08-30. Sources: official Track 2 PDF (pp. 3-9), the supplied Starter Kit, and the official Devpost event page.

## Release position

The current branch is technically ready for review and can be made public **without** publishing the organizer materials. The whole `kuairand-starter-kit/` directory is ignored. The local KuaiRand data directories contain CC BY-SA 4.0 license text; the separate Starter Kit source files contain no code-license notice. This is not legal advice: the safe release position is to redistribute neither data nor Starter Kit source, and direct users to the organizer materials.

## Rubric evidence

| Criterion | Weight | Evidence we have | Remaining exposure |
|---|---:|---|---|
| Technical Execution | 35% | 71 data-free tests; organizer-evaluator delegation; fail-closed test policy; frozen checkpoint/output chain; 27K resumability; R028 recovery proof. | Official score is unproven because the benchmark contract is internally inconsistent. |
| Innovation & Problem Insight | 20% | Bounded research controller; papers/evidence cards; BPR/listwise, history, multi-task, backbone, scale and frozen-ensemble comparisons; retained regressions. | Explain the selection logic visually in the video/pitch. |
| Impact & Relevance | 20% | End-to-end campaign has zero mid-run human interventions; append-only run/decision evidence. | Show the autonomous loop, not merely static result tables, in the demo. |
| Feasibility & Practicality | 15% | Measured campaign has 0 LLM input/output tokens and 0 GPU-hours; CPU-scale 27K streaming/resume; resource records. | Clearly frame zero GPU use as a deliberate laptop-friendly design, not an omitted measure. |
| Presentation & Communication | 10% | README, Devpost draft, demo script, results log, and architecture narrative. | Record and publish the required public 3-minute YouTube demo before Devpost submission. |

## Benchmark and score audit

The PDF contains a material contradiction:

- Pages 3, 4, 6, 7, and 8 repeatedly describe click / NDCG@10 / Recall@50.
- Page 5 says the downloaded Starter Kit is the exact evaluator and pins `long_view`, GAUC, nDCG@5, epsilon `0.002`, N `3`, the FM baseline, and the output schema.
- Page 6 also says the exact label and K values are pinned in the Starter Kit.

**Interpretation - not explicit organizer wording:** D029/D031 use the versioned Starter Kit as the executable internal contract. Under it, the reproduced five-seed validation baseline is primary `0.601572`; the frozen BPR/history/temporal ensemble is `0.604017`, a validation delta of `+0.002445`. R027 binds that exact checkpoint to a schema-valid 170,588-row feature-only output. These are not NDCG@10 / Recall@50 results, a hidden-test score, or organizer confirmation.

Do not change the Devpost wording from “team-interpreted” unless organizers provide an unambiguous contract. If they provide a changed evaluator, create a new profile and rerun affected validation/campaign evidence rather than comparing scores across profiles.

## Mandatory external deliverables

1. Push the reviewed branch, open the PR, and wait for the data-free CI run.
2. Merge after review and make the repository public; it contains no organizer code or data.
3. Record and publish a public 3-minute YouTube end-to-end demo, then add its URL to Devpost.
4. Submit the Devpost description, public repository URL, demo URL, run logs/resources, and the exact final output/checkpoint as directed by organizers.
5. Keep the metric clarification request open. The official Devpost deadline currently states **1 September 2026, 12:00 pm SGT**.

## Pre-submission checks

- Preserve the final output hash: `60538bb59c96547bfb3e8f90ff56d8c0b5b2e2002c38ba708ecf5e2dfe82a672`.
- Preserve the final checkpoint hash: `85bc25dbb1469ab043896b4f3872a295521908f85a1794db747b446399921c2f`.
- Do not score or inspect local test labels.
- Do not publish `kuairand-starter-kit/` or any `artifacts/` content without first removing any organizer-derived material and checking terms.
