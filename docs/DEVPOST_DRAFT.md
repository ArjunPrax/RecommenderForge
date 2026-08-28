# Devpost Draft — Autonomous Recommender Research Agent

Status: Draft for human submission. Metrics are validation-only under the provisional Starter Kit evaluator; do not claim organizer-hidden-test performance.

## Inspiration

Recommender-system iteration often requires a person to turn a hypothesis into a code change, run the benchmark, diagnose a regression, keep the useful evidence, and repeat. Track 2 asks for that research loop to become an accountable system rather than an opaque collection of experiments.

## What it does

Our project is an autonomous ML research control plane for TikTok recommender benchmarks. It:

- reproduces a safe validation-only organizer baseline;
- proposes bounded, evidence-backed candidate experiments;
- trains/evaluates only permitted development splits through the organizer evaluator;
- blocks test-label access structurally and generates output from frozen checkpoints only;
- records hypotheses, source evidence, configuration/code/data/evaluator identities, metrics, failures, recovery, resource use, and interventions in an append-only ledger;
- evaluates convergence by candidate batch rather than incorrectly treating siblings as sequential iterations;
- produces a campaign report and can designate the exact converged checkpoint for feature-only submission generation.

## Why it matters

The point is not merely to find a higher validation number. It is to make autonomous iteration credible: every model result has provenance, regressions remain visible, recovery is evidence, and the final output is traceable to the checkpoint that earned its validation result.

## Technical approach

The initial benchmark implementation uses the supplied KuaiRand-Pure starter evaluator as a provisional executable contract while an organizer metric/label ambiguity is tracked openly. The agent reproduced the pointwise FM, established a PyTorch parity gate, evaluated pairwise BPR, grouped listwise ranking, strict train-only history crosses, a temporal cross, multi-feedback learning, watch-completion supervision, a compact DeepFM backbone, denser BPR sampling, and frozen rank ensembles.

The current validation leader is a frozen BPR/history/temporal rank blend with mean primary `0.604017`, compared with the reproduced pointwise baseline `0.601572` (+`0.002444`). This is not a hidden-test result and is not yet a final designated submission.

For bonus-scale artifacts, the agent streams KuaiRand-1K and KuaiRand-27K data, avoids loading test labels, uses bounded item statistics, and evaluates validation in user-consistent shards. KuaiRand-1K preflight and baseline are completed; 27K preflight is in progress at the time of this draft.

## Evidence and autonomy

The codebase has deterministic qualification evidence, controlled recovery evidence, safe worktree/diff controls, checkpoint manifests, per-run resource accounting, and campaign-level convergence/finalization checks. Recorded research runs used zero mid-run manual interventions. The default planner is deterministic and offline, so the recorded runs honestly report zero LLM tokens; the provider boundary is explicit rather than fabricating LLM use.

## Tools and assets

- Python 3.13, NumPy, and PyTorch
- SQLite append-only evidence ledger
- Organizer-supplied KuaiRand-Pure, KuaiRand-1K, and KuaiRand-27K data/artifacts
- Organizer-supplied evaluator and Starter Kit
- Git worktrees and content hashes for isolated, reproducible candidate evidence

No external training data or pretrained recommender weights are used.

## Challenges and lessons

The supplied PDF narrative and runnable Starter Kit conflict over the label and metric contract. Rather than hiding that ambiguity, the implementation versions the evaluator hash, labels the current profile provisional, and blocks final metric-specific claims until organizers clarify. Several plausible candidates regressed; retaining those results made the final evidence stronger and prevented accidental cherry-picking.

## Next steps before submission

1. Complete the checksum-verified KuaiRand-27K preflight/baseline.
2. Complete a clean, explicit campaign from an immutable leader through its declared convergence point.
3. Generate the final output from the campaign-designated checkpoint without retraining or test scoring.
4. Update the benchmark contract if organizers resolve the evaluator ambiguity.
5. Publish the reviewed repository and replace this draft's provisional wording with measured final evidence.
