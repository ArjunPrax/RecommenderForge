# Devpost Draft — Autonomous Recommender Research Agent

Status: Draft for human submission. Metrics are validation-only under the organizer-confirmed Starter Kit contract; do not claim organizer-hidden-test performance.

The official Devpost event also requires a public 3-minute YouTube demo. The script is in `docs/DEMO.md`; record and add the public URL before submission.

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

The organizers confirmed that the checked-in Starter Kit is authoritative: native `long_view`, within-user GAUC/nDCG@5, and primary equal to their mean. `evaluate.py` is the exact scorer; earlier click/NDCG@10/Recall@50 wording is superseded. The agent reproduced the pointwise FM, established a PyTorch parity gate, evaluated pairwise BPR, grouped listwise ranking, strict train-only history crosses (including user-author affinity), a temporal cross, multi-feedback learning, watch-completion supervision, a compact DeepFM backbone, denser BPR sampling, and frozen rank ensembles.

The validation leader is a frozen BPR/history/temporal rank blend with mean primary `0.604017`, compared with the reproduced pointwise baseline `0.601572` (+`0.002445`). It was revalidated inside a declared campaign with one common data fingerprint/evaluator and three subsequent non-significant confirmation batches. The confirmed campaign designated its exact checkpoint and generated a 170,588-row, schema-valid feature-only output without retraining. This is not a hidden-test result or an official submission.

For bonus-scale artifacts, the agent streams KuaiRand-1K and KuaiRand-27K data, avoids loading test labels, uses bounded item statistics, and evaluates validation in user-consistent shards. Both artifacts are checksum/preflight verified. The 1K item×tab blend reached validation primary `0.545843` and generated a checkpoint-backed feature-only output for all 4,132,081 test rows. The 27K item×tab baseline reached validation primary `0.586756`, generated a checkpoint-backed feature-only output for all 114,832,239 test rows, and proved a real interruption/resume path produces the exact same full-file SHA-256. This is scale and robustness evidence, not a claim of beating an organizer bonus threshold: no 1K/27K reference, threshold, or upload route has been provided.

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

The organizers resolved the earlier wording conflict in favor of the Starter Kit. The implementation retains the evaluator hash and historic pre-confirmation records, while the current campaign is explicitly confirmed. Several plausible candidates regressed; retaining those results made the final evidence stronger and prevented accidental cherry-picking.

## Next steps before submission

1. If organizers issue a corrected evaluator, create its new profile and repeat affected validation/campaign work.
2. Complete human review, public-repository publication, and official competition submission.
3. Do not replace the validation-only result with a hidden-test claim until the official competition service returns one.
