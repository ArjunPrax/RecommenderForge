# Organizer Benchmark Confirmation

Date received: 2026-08-31

Source: organizer response supplied in the project conversation. This records the confirmed contract; it does not create a hidden-test score.

## Confirmed authority

The checked-in Starter Kit is the scoring authority. Its `evaluate.py` is the exact scoring code.

| Contract field | Confirmed value |
|---|---|
| Prediction target | Native `long_view` column |
| Ranking scope | Within each user's logged impressions |
| Metrics | GAUC and nDCG@5 |
| Primary | Mean of GAUC and nDCG@5 |
| Official baseline | NumPy Factorization Machine: k=16, lr=0.001, five categorical fields |
| Convergence | epsilon = 0.002; N = 3 |
| Output schema | `row_id,user_id,video_id,score` |

The organizers state that all earlier references to `click`, NDCG@10, and Recall@50 are superseded. Recall@50 is not meaningful here because users have only about five logged impressions in the evaluation split.

## Reference figures supplied by organizers

| Result | GAUC | nDCG@5 | Primary |
|---|---:|---:|---:|
| FM hidden test, mean of five seeds | 0.6610 | 0.5282 | 0.5946 |
| FM validation | 0.6674 | 0.5357 | 0.6016 |
| Random scoring, hidden-test primary | — | — | 0.4753 |
| Item popularity, hidden-test primary | — | — | 0.5715 |

The message also supplies an oracle primary ceiling of `0.8645`: 27.1% of test users are all-negative and 9.2% are all-positive. These reference figures must not be reproduced locally by accessing or scoring hidden-test labels.

## Consequences for this repository

The existing KuaiRand-Pure code, validation campaign, and output already use the confirmed Starter Kit definition. The confirmed campaign therefore reuses the immutable validation records and frozen checkpoint; it does not retrain or inspect test labels. Historical provisional/team-interpreted records remain in `results_log.md` as an accurate record of the state before this response.
