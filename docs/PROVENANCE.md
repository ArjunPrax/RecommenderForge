# Data and model provenance

## Declared inputs

- Organizer-supplied KuaiRand-Pure, KuaiRand-1K, and KuaiRand-27K artifacts only. Archive checksums and artifact counts are recorded in `results_log.md`.
- Organizer-supplied evaluator only. Each research run binds its evaluator SHA-256 in the append-only ledger.
- No external training data, pretrained recommender weights, embeddings, or downloaded model checkpoints are used.

## Enforcement

- Candidate-facing adapters never materialize test labels and reject test scoring.
- Auxiliary and watch-time outcomes are exposed only for training rows.
- Every campaign requires a single evaluator hash and a single data fingerprint.
- Submission writers load frozen measured artifacts and publish outputs atomically; they do not retrain or score test labels.

## Scope

This declaration reflects the implemented and logged runs. The local KuaiRand data directories contain CC BY-SA 4.0 license text; the separately supplied Starter Kit source contains no separate code-license notice. The entire `kuairand-starter-kit/` directory is intentionally git-ignored and protected by a repository-safety test. The public repository excludes both the kit and data rather than relying on redistribution permission. This is a release-scope record, not legal advice.
