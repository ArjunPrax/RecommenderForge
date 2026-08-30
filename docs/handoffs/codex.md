# Codex Handoff

## Current task

T2-004 — complete the autonomous qualification workflow after T2-002 foundation review.

## Current truth

- Updated PDF removes AliCCP but conflicts over KuaiRand target/metrics.
- Starter Kit evaluator is provisional; test labels must remain inaccessible to candidate code.
- KuaiRand-Pure was downloaded from the official Zenodo release and verified against the published MD5.
- R001 reproduced the five-seed NumPy FM validation reference without local test scoring.
- R002 passed fixed-weight, one-step, and five-seed NumPy-to-PyTorch pointwise parity.

## Next platform deliverables

1. Integrate Git worktrees into the qualification executor.
2. Add an LLM-planner boundary and first ranking-objective plugins.
3. Run the qualification workflow as a tracked ledger result.

## Risks

- Do not use the starter kit's local test-score route.
- Keep external/data artifacts ignored.
