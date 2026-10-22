# 06: Run integrity

- **Found by:** an independent read-only review of the repo on 21 Oct 2026, 21:13-21:18 IST. Numbers and paths below come from that review, which checked them against the repo's results files.

## Issue and evidence
Run integrity: two double-driver incidents and two VM losses. The final file is 2,231 rows from one driver plus 1,549 resumed on a new VM with vLLM 0.31.0 and an explicit xgrammar flag. The disclosure is thorough, and block-wise results look consistent.

## Status
Open, documented. Nothing in the results was changed because of it. The README/writeup or the blog post states where it changes how the result should be read. Any fix needs a new pre-registered run on fresh data (hypothesis rules), not an edit to these numbers.
