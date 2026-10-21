# 01 (133): Several hypotheses test harness code, not agent behaviour

- **Experiment:** 133 (this repo)
- **Found by:** an independent read-only review of the repo on 21 Oct 2026, 21:13-21:18 IST (fact sheet `133-agent-seven-architectures.md`). Numbers and paths below come from that review, which checked them against the repo's results files.

## Issue and evidence
Several hypotheses test harness code, not agent behaviour. Their outcomes are set by construction: H5 (V4 crash dup 100% [100,100]): the side-effect node commits and crashes before its checkpoint write, so resume always re-runs it. That is deterministic, and the CI is degenerate. H1's V7 = 0% is guaranteed by a mock idempotency dict that is honoured perfectly. H4's V4 = +0.0 is deterministic resume. H7 measures overlapping 0.25 s mock sleeps. V2/V3/V5 timeout success 0% / dup 97% come from the pre-registered "restart from scratch on any failure" runner plus commit-then-timeout mocks. Only H2, H3, H6, H8 and V1's numbers really depend on LLM behaviour. "7 of 8 PROVEN" overstates what was learned empirically.

## Status
Open, documented. Nothing in the results was changed because of it. The README/writeup or the Substack post states where it changes how the result should be read. Any fix needs a new pre-registered run on fresh data (hypothesis rules), not an edit to these numbers.
