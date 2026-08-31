# Organizer clarification email draft

> Historical draft. The organizers answered the metric, baseline, convergence, and evaluation questions on 2026-08-31; see [ORGANIZER_CONFIRMATION.md](ORGANIZER_CONFIRMATION.md). Keep this record for provenance only.

**To:** [TechJam organizer email]

**Subject:** Clarification on Track 2 benchmark, metrics, and submission contract

Dear TechJam Organizing Team,

Our team has started implementing the Track 2 autonomous recommender-system research agent and has reproduced the supplied KuaiRand-Pure starter baseline on the validation split. Before we prepare the final campaign and submission, we would appreciate clarification on a few points where the track document and the runnable starter materials appear to describe different evaluation contracts.

1. Which benchmark is authoritative for Track 2 final scoring: KuaiRand-Pure using `long_view`, or the click-prediction formulation described elsewhere in the document? If both are required, could you confirm their relative weighting?

2. Which metric should our agent optimise and report as the primary metric: the starter kit's GAUC and nDCG@5 average, or nDCG@10 and Recall@50? Please also confirm the exact validation and hidden-test evaluation procedure.

3. For the KuaiRand-1K and KuaiRand-27K bonus benchmark, what is the reference score or threshold that must be beaten, and which dataset split/evaluator will be used to determine this? We have verified the artifacts and built bounded-memory baseline/output paths, but do not want to claim the bonus without the official reference.

4. Could you clarify the convergence rule? In particular, for epsilon = 0.002 and N = 3, what counts as one iteration: a single candidate, a batch of sibling candidates from the same parent, a failed/recovered candidate, or a checkpoint/output regeneration?

5. Please confirm the final submission process: whether a checkpoint is required in addition to predictions, the permitted number of submissions, and the final deadline/time zone. We will retain the Starter Kit's supplied `row_id,user_id,video_id,score` schema unless you specify otherwise.

6. The KuaiRand data directories include CC BY-SA 4.0 license text, but the separately supplied Starter Kit source has no separate code-license notice. May we include any unmodified Starter Kit source in our required public repository, or should teams keep the kit excluded and link users to the organizer download?

These answers will help us keep our implementation and reporting aligned with the intended competition contract. Thank you for your guidance.

Best regards,

Arjun and team
