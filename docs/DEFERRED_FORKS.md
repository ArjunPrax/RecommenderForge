# Deferred Forks and Late Refinements

Purpose: retain reviewed refinements and their evidence. The agreed implementation is plan **v4**; apply-now items are incorporated through D006-D011 and T2-002.

Source: independent review of plan v3 (2026-08-26). Every number below was verified against the
Starter Kit source, `baseline_scores.json`, or the updated official PDF
(SHA-256 `a940266486f5b3b320f932b4261470c986f47d8d5d9d3f484b645225b9ee82ff`).

**ID scope.** `FORK-XX` identifiers are local to this document. They are **not** `EXP-XXX`,
`T2-XXX`, `DXXX`, or `RXXX` identifiers. If a fork is promoted into real work, assign a stable ID at
that point. Do not cite `FORK-XX` in commits, PRs, or `results_log.md`.

---

## Disposition summary

| ID | Item | Disposition | Latest safe point to act |
|---|---|---|---|
| FORK-01 | Inner-dev split is doing two different jobs | **Deferred** — v3's mandatory use is already correct | Any time |
| FORK-02 | Wave 2 exit criteria depend on Wave 3 deliverables | **Apply now** | Before Wave 1 closes |
| FORK-03 | Parity Gate B tolerance is too loose | **Apply now** | Before Gate B is run |
| FORK-04 | No `run_class` on `RunRecord`; resource boundary unstated | **Apply now** (cheap) | Before the first ledger record exists |
| FORK-05 | `EXP-XXX` numbers were reassigned between v2 and v3 | **Apply now** (free) | Before IDs land in `docs/EXPERIMENTS.md` |
| FORK-06 | GPU-hours headline should be MPS + CUDA | **Deferred** — reporting decision | Wave 7 |
| FORK-07 | Exact listwise objective is affordable at these list lengths | **Deferred** — research fork | Wave 3-4 |

Three of these (FORK-02, FORK-03, FORK-05) are cheap now and expensive or impossible later. They are
recorded here for completeness but are **not** intended as deferred work. The genuinely optional
items are FORK-01, FORK-06, and FORK-07.

---

## FORK-01 — The inner-development split is doing two different jobs

**Disposition: deferred. v3's mandatory use of the split is correct; only the pruning use is open.**

v3 §6 defines the inner split as `20220408-20220417` (inner train) / `20220418-20220421` (inner dev),
then has candidates train on inner-train, evaluate on inner-dev, and "promote plausible candidates"
to full train / official validation.

That is two separable jobs:

- **Job A — early stopping and hyperparameter selection inside `fit()`.** Keeps the official
  validation period from being consumed as a training signal. This is the reason the split was
  requested. It is mandatory in v3 and should stay mandatory.
- **Job B — rejecting candidates before they ever reach official validation.** This is a fidelity
  proxy.

Job B conflicts with v3's own multi-fidelity policy in the same section ("No 2% or 20% proxy may
reject a candidate initially... only after demonstrating useful rank correlation"). Temporal
truncation is more principled than random row subsampling, but the failure mode is the same in kind:
the inner-dev model trains on 10 of 14 days, so its `user_id x video_id` coverage differs from the
promoted model's, and the Starter Kit states that this crossing carries most of the learnable signal.
The inner-dev model is therefore **a different model** from the one that gets promoted, and its
ranking of candidates need not agree.

Job B also buys nothing at Pure scale: the official FM trains in ~40 s on one CPU core, and a torch
ranking model over 1,141,112 training rows is minutes.

**Recommended default (no experiment needed):** keep Job A, drop Job B, run every candidate at full
fidelity. This makes §6 internally consistent at zero cost.

**If Job B is wanted anyway, the settling experiment is:**
run 3+ structurally different models (pointwise FM, pairwise FM, a history-cross model) x 3 seeds,
scoring each on both inner-dev and full official validation, and report Spearman rank correlation of
the candidate ordering. Job B is admissible only if that correlation is high enough that proxy
rejection would not have discarded the eventual winner. This is the same bar v3 already sets for the
5%/20%/100% row-subsample ladder.

**Measure before assuming:** 10 of 14 days is a share of *days*, not of rows. Record the actual row
share after download.

---

## FORK-02 — Wave 2 exit criteria depend on Wave 3 deliverables

**Disposition: apply now. Wave 2 cannot pass as written.**

- Wave 1 gives the implementation a "minimal controller".
- Wave 2 exit requires an injected failure recovering automatically, an `epsilon`/`N` convergence
  rehearsal, and automatic judge-facing report generation.
- Wave 3 lists deliverables as "automated promotion, rejection, **recovery, and convergence**".

Recovery, convergence evaluation, and report generation are therefore scheduled *after* the wave
whose exit criteria require them.

**Change:** move the recovery state machine, the convergence evaluator, and the report generator into
**Wave 1**. Wave 3 then adds LLM-driven research-tree selection and reflection on top of a
deterministic loop that already runs end to end. Either that, or rename Wave 1's "minimal controller"
to state that it contains these three components — but they must exist before Wave 2 is attempted.

This defect was introduced by pulling the qualification run earlier (an accepted review point); the
dependency was not propagated to the wave table.

---

## FORK-03 — Parity Gate B tolerance is set from an unrelated quantity

**Disposition: apply now. Must be fixed before Gate B is run.**

v3 §7 accepts the PyTorch port when the 5-seed mean validation primary is within **0.002** of NumPy.
`0.002` is `epsilon`, the organizer convergence threshold. It has no relationship to implementation
parity, and it is large relative to what the project is trying to detect:

| Quantity | Value | Source |
|---|---:|---|
| Per-seed std of baseline primary | 0.0008 | `baseline_scores.json` (5 seeds, test) |
| Standard error of a 5-seed mean | ~0.00036 | derived |
| ~2 SE band | ~0.0007 | derived |
| Proposed Gate B tolerance | 0.002 | v3 §7 |
| Research target improvement | +0.004 | v3 §9 (0.6016 -> 0.6056) |

A torch port that is 0.0018 *worse* than NumPy passes the gate as written — roughly half the target
improvement, absorbed silently. The baseline that must actually be beaten is the organizer's **NumPy**
FM, so any parity gap propagates directly into the final claim.

**Change:**

1. Set the pass bar to **<= 0.001** on the absolute difference of 5-seed mean validation primary.
2. Add a **sign test**: the difference must not be directional. A torch port that lands below NumPy on
   all five seeds is a defect (Adam epsilon placement, L2 semantics, batch handling, early-stopping
   tie-break), not noise, even at 0.0005 magnitude.
3. If a residual gap survives, record it as a **known offset** and carry it into every downstream
   comparison and into the final result table.

v3's separate instruction to retain a pointwise torch control for loss experiments is correct and
should stay; it handles attribution *within* the torch lane but not the comparison against the
organizer baseline.

---

## FORK-04 — Qualification-run records are indistinguishable from research records

**Disposition: apply now while it is a schema change with no rows to migrate.**

Wave 2's system qualification run produces a full report, a submission file, an intervention count,
and token/CPU/MPS totals — from a run v3 explicitly labels non-final. Nothing in `RunRecord`
distinguishes it from the designated final run.

**Change:**

1. Add `run_class` to `RunRecord`: `qualification` | `research` | `designated_final`.
2. State the resource-accounting boundary explicitly. The PDF asks for resource usage "required to
   reach the converged result." Qualification-run tokens and compute either count or they do not;
   either choice is defensible, silence is not.
3. Same for the manual-intervention counter. The qualification run deliberately injects a failure and
   will carry human touches that must not be folded into the autonomy figure. Judges will reasonably
   ask which run the count describes.

---

## FORK-05 — `EXP-XXX` identifiers were reassigned between plan v2 and v3

**Disposition: apply now. Free today, a governance violation later.**

| ID | Plan v2 meaning | Plan v3 meaning |
|---|---|---|
| EXP-002 | ranking objectives | PyTorch pointwise parity |
| EXP-003 | history / temporal crosses | ranking objectives |
| EXP-004 | multi-task | history and temporal crosses |
| EXP-005 | watch-time / duration | multi-feedback |
| EXP-006 | exposure bias | watch-time / duration bias |
| EXP-007 | ensembles | exposure and temporal robustness |
| EXP-008 / 009 | 1K / 27K scaling | ensembles / scaling |

Stable, never-recycled IDs ensure that cancelled work retains its ID. No harm
has occurred yet: neither plan was committed, and the repository is still at the two bootstrap
commits. But once these numbers reach `docs/EXPERIMENTS.md` both agents will cite them across
branches, PRs, and `results_log.md`, and renumbering becomes a real violation.

**Change:** assign the `EXP-XXX` numbers exactly once, in Wave 0, and never shift them. Insert new
families at the end of the sequence rather than renumbering.

---

## FORK-06 — GPU-hours headline figure

**Disposition: deferred to Wave 7. Reporting decision, not a build decision.**

v3 §11 correctly refuses to claim "0 GPU-hours" when Apple MPS is used — this is better than the
framing it replaced. The remaining issue is presentation: `RunRecord` and §11 both list MPS-minutes
and CUDA-hours as parallel categories, which risks a headline figure that understates.

On Apple silicon, MPS time is GPU time.

**Change at report time:** report `GPU-hours = MPS + CUDA` as the single deliverable figure the PDF
asks for, with the split shown beneath it. A small number honestly labelled is stronger than a
smaller number that reads as evasive. The preferred claim in v3 §11 — full autonomous convergence on
a single consumer laptop with no rented accelerator — is unaffected and remains the right framing.

---

## FORK-07 — Exact listwise objective is affordable at these list lengths

**Disposition: deferred research fork. Cheap to test; run it alongside BPR if Wave 3 allows.**

The evaluation lists are unusually short:

| Split | Rows | Users | Rows per user |
|---|---:|---:|---:|
| train | 1,141,112 | ~27K | ~42 |
| valid | 124,909 | (measure) | (measure) |
| test | 170,588 | 23,875 | **7.15** |

Row counts from PDF p.5; test user count from the Starter Kit README.

At ~7 impressions per user, `nDCG@5` covers 5 of about 7 items and GAUC operates over ~7-item lists.
Per-user training lists are short as well.

Sampled pairwise BPR is the standard opening move because full lists are usually intractable. Here
they are not. An **exact listwise softmax over a user's full impression list** is computable with no
negative sampling and no pair construction, and the objective is directly the quantity being scored.

**Fork:** run exact listwise as a sibling of BPR in the first ranking-objective wave rather than
holding it as a later option, and let the measurement decide. It removes the pair sampler as a source
of defects, and the same within-user assertion v3 already specifies covers it.

This does not displace anything in v3 — listwise soft-NDCG is already listed among the ranking
objectives. The fork is only about **promoting it to a first-round candidate**.

---

## Not deferred — already agreed and in v3

Recorded so the disposition is unambiguous:

- Smoke runs make no metric decisions; no proxy may reject a candidate without demonstrated rank
  correlation.
- Random-exposure audit is restricted to `20220422-20220428`.
- Test-label access is structurally blocked and audited; `submit.py --score --split test` is unused.
- Convergence ships the validation-best checkpoint; the internal target never blocks submission.
- No retraining on train+validation; the submitted model is the measured model.
- Every feature family must demonstrate a within-user ordering effect.
- 1K and 27K are gated on official artifacts, not on schedule.
- AliCCP is out of scope: it is absent from the updated PDF (0 occurrences across 12 pages).
