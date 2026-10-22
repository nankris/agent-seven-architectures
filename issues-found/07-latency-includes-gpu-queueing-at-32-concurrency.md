# 07: Latency includes GPU queueing at 32 concurrency

- **Found by:** an independent read-only review of the repo on 21 Oct 2026, 21:13-21:18 IST. Numbers and paths below come from that review, which checked them against the repo's results files.

## Issue and evidence
Latency includes GPU queueing at 32 concurrency (H7 CI 0.34-1.42 s). H7 passes, but noisily.

## Status
Open, documented. Nothing in the results was changed because of it. The README/writeup or the blog post states where it changes how the result should be read. Any fix needs a new pre-registered run on fresh data (hypothesis rules), not an edit to these numbers.
