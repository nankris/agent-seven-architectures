# 02 (133): Faults are synthetic and friendly to idempotency keys

- **Experiment:** 133 (this repo)
- **Found by:** an independent read-only review of the repo on 21 Oct 2026, 21:13-21:18 IST (fact sheet `133-agent-seven-architectures.md`). Numbers and paths below come from that review, which checked them against the repo's results files.

## Issue and evidence
Faults are synthetic and friendly to idempotency keys (writeup admits this). The "crash" is a Python exception inside one process with the ledger held in memory. There is no real process death, no provider-side duplicate and no network.

## Status
Open, documented. Nothing in the results was changed because of it. The README/writeup or the Substack post states where it changes how the result should be read. Any fix needs a new pre-registered run on fresh data (hypothesis rules), not an edit to these numbers.
