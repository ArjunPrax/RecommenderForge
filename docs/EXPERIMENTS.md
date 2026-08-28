# Experiment Registry

Plan experiments here; measured outcomes belong in `results_log.md`. IDs are stable and must never be reassigned.

| ID | Title | Status |
|---|---|---|
| EXP-001 | Organizer baseline reproduction | Planned |
| EXP-002 | NumPy-to-PyTorch pointwise parity | Planned |
| EXP-003 | Autonomous qualification run | Planned |
| EXP-004 | Ranking objectives: BPR and exact listwise | Measured manually; autonomous rerun pending. Child candidates: EXP-004A (BPR), EXP-004B (exact listwise). See R003 and R004. |
| EXP-005 | Candidate-specific history and temporal crosses | Measured; see R005 (recovered run) and R006 |
| EXP-006 | Multi-feedback learning | Measured; R007 rejects the first shared-FM auxiliary configuration |
| EXP-007 | Train-only watch-completion auxiliary objective | Measured; R013 rejects the first configuration |
| EXP-008 | Exposure and temporal robustness | Measured; see R009 |
| EXP-009 | Ensembles | Measured; R008 two-component, R010 three-component child EXP-009A historical leader. EXP-009B–D were excluded from campaign use after a data-fingerprint mismatch; EXP-009E revalidated the frozen leader, and EXP-009F–H establish the converged provisional campaign in R023. |
| EXP-010 | KuaiRand-1K scale validation | Baseline demonstrated on official artifact; R012 |
| EXP-011 | KuaiRand-27K scale validation | Official archive checksum/preflight and bounded streaming baseline demonstrated; R016/R017 |
| EXP-012 | Compact DeepFM BPR backbone | Measured; R011 rejects the first configuration |
| EXP-013 | Three-negatives-per-positive BPR sampling | Measured; R014 rejects the first configuration |
| EXP-014 | Top-five-aware Lambda-BPR mixture | Measured; R015 rejects the fixed 50/50 mixture |
| EXP-015 | Bounded item×tab popularity scale candidate | Checkpointed 27K validation/output chain and frozen 3-weight grid demonstrated; R018–R021 |
| EXP-016 | Strict-prior video×tab candidate-history cross | Measured; R022 rejects it against the BPR parent while retaining its integrity evidence. |

## EXP-XXX - Experiment title

Status:
Owner:
Run class: qualification / research / designated_final
Operator family:
Parent experiment / checkpoint:

### Question

### Hypothesis

### Motivation

### Baseline

### Variable being changed

### Controlled variables

### Metrics

### Success criteria

### Procedure

### Reproduction command

### Result

Link to RXXX in `results_log.md`.

### Conclusion
