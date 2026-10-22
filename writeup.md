# Writeup: one refund agent, seven LangGraph architectures, under failure

**Verdict: H1 (primary) PROVEN.** Of the 8 pre-registered hypotheses, 7 are PROVEN and 1 is DISPROVEN (H6, "accuracy is a tie when nothing fails").

**Headline number: 63% vs 0%.** Under an API timeout or a crash, the plain ReAct loop sent a refund, credit or ticket twice in 63% of runs. The full graph (checkpointing, retries and idempotency keys) did it in 0% (difference 62.8 pp, 95% CI 58.9 to 66.9).

**Takeaway.** The thing that stops an agent from paying twice is the idempotency key on each side effect, not the graph, and not checkpointing: checkpointing alone duplicated a side effect in 100% of crashed runs. Breaking the agent into a structured graph cut model calls by 65% and prompt tokens by 91%, and on Qwen3-8B it was also far more accurate (93% vs 57% with no faults at all).

Builds on Brahim Guaali, [I rebuilt one AI agent seven times to understand graph engineering](https://medium.com/@brahimg/i-rebuilt-one-ai-agent-seven-times-to-understand-graph-engineering-80b9983cd921) and its code [graph-engineering-from-first-principles](https://github.com/brahim-guaali/graph-engineering-from-first-principles).

## Setup (summary; full pre-registration in README.md)

- Job: food-delivery refund agent (the source's job). 60 fresh confirmatory tasks (T01-T60) over 9 case types, never used in the 12-task pilot. Mock side-effect tools (refund, $5 credit, ticket, email) write to a ledger.
- 7 architectures (LangGraph 1.1) x 3 conditions (no fault, API timeout with lost acknowledgement, process crash and resume) x 60 tasks x 3 seeds = **3,780 runs**, fully paired.
- Model: Qwen3-8B (FP8) on vLLM, Hermes tool calling, thinking off, temperature 0.7. 12,647 model calls, 7.37M prompt and 0.61M completion tokens (vLLM `usage` field).
- Statistics: unit = task (mean over 3 seeds), paired across architectures, 95% percentile bootstrap over the 60 tasks, 10,000 resamples. Decision rule pre-registered: PROVEN if the whole CI is beyond the margin in the predicted direction, DISPROVEN if wholly on the other side.

## Pre-registered hypotheses (figures/table.png)

| # | Metric | Prediction (source) | Estimate [95% CI] | Margin | Verdict |
|---|---|---|---|---|---|
| H1 | duplicate money effect rate, V1 minus V7, faulted runs | V7 ~0, V1 well above | **+62.8 pp [58.9, 66.9]** | 5 pp | PROVEN |
| H2 | model-call reduction V1 to V2, no fault | -41% | **64.9% [61.9, 67.2]** | 25% | PROVEN |
| H3 | prompt-token reduction V1 to V2, no fault | -78% | **90.6% [89.7, 91.3]** | 50% | PROVEN |
| H4 | extra model calls after a crash, V3 minus V4 | ~2 vs 0 | **1.90 [1.82, 1.97]** | 1 call | PROVEN |
| H5 | V4 (checkpoint only) duplicate rate after a crash | high ("paid twice") | **100% [100, 100]** | >50% | PROVEN |
| H6 | success V7 minus V1, no fault (equivalence) | tie (12/12 vs 12/12) | **+35.0 pp [21.1, 48.3]** | +-10 pp | **DISPROVEN** |
| H7 | latency V2 minus V3 (parallel lookups), no fault | ~0.5 s | **0.83 s [0.34, 1.42]** | 0.25 s | PROVEN |
| H8 | success V7 minus V1 under the timeout | positive | **+92.2 pp [85.6, 97.8]** | 10 pp | PROVEN |

## Per-architecture results (figures/table_archs.png; means over 60 tasks x 3 seeds)

| Architecture | Success no fault | Success timeout | Success crash | Dup. timeout | Dup. crash | Model calls (no fault) | Prompt tokens (no fault) | Latency s (no fault) |
|---|---|---|---|---|---|---|---|---|
| V1 ReAct loop | 57% | 0% | 0% | 30% | 96% | 5.4 | 6,752 | 14.7 |
| V2 + structured state | 93% | 0% | 0% | 97% | 97% | 1.9 | 635 | 7.7 |
| V3 + parallel nodes | 93% | 0% | 0% | 97% | 98% | 1.9 | 635 | 6.9 |
| V4 + checkpointing | 92% | 0% | 0% | 100% | 100% | 1.9 | 635 | 7.2 |
| V5 + human approval | 93% | 0% | 0% | 97% | 97% | 1.9 | 635 | 7.1 |
| V6 + retries + idempotency keys | 93% | 93% | 91% | 0% | 0% | 1.9 | 635 | 6.9 |
| V7 full combination | 92% | 92% | 92% | 0% | 0% | 1.9 | 635 | 7.1 |

Other numbers from `results/summary.json` and the raw rows:

- Recovery cost. After a crash, V4 and V7 resumed from the checkpoint with no extra model calls (1.9 per run, same as no fault). V2, V3, V5 and V6 restart from scratch: 3.8 calls per crashed run. V1 rose from 5.4 to 9.2 calls and from 6,752 to 11,130 prompt tokens.
- Money. Summed over all faulted runs, the agents paid out more than the correct amount by: V1 $71,212; V2 $36,900; V4 $36,725; V6 $1,574; V7 $1,488. The V6/V7 residual is wrong refund decisions by the model (for example on missing-item claims), not duplicates: their idempotency stores absorbed 356 and 360 repeated side-effect attempts.
- V1 under the timeout fails differently. Only 30% of its timeout runs duplicated a side effect, but 0% succeeded: after the fraud lookup timed out, the model often went off-policy (opened a ticket instead of refunding, skipped the credit). Retrying is not the only way a loop goes wrong.
- V1 with no faults lost most often on cancelled orders (3/18), complaints (0/18), prompt injection (0/18) and "slightly late" (6/21), mainly through wrong refund/credit amounts or a missing notification. V7 lost mainly on missing-item (17/24) and slightly-late (15/21) tasks.
- Faults fired as designed in every faulted run of every cell (`fault_fired` in `results/summary.json`). 0 failed model calls and 0 harness errors in 3,780 runs.

## Caveats

- **The faults are friendly to idempotency keys by construction.** Side effects commit and then lose the acknowledgement, and the mock honours keys perfectly. Real payment APIs need the key passed through to the provider; a key that only lives in your process does nothing for a provider-side duplicate.
- **V2-V5 duplicate almost always because our runner restarts them from scratch** after any failure (pre-registered "any failure: restart the run"). A smarter runner that stops on the first error would duplicate less and finish fewer tasks. V1 instead lets the model decide whether to retry, which is why its timeout duplicate rate is lower.
- **H6 is a miss.** The source saw a 12/12 tie with Gemini. Qwen3-8B in a free-form ReAct loop is much weaker than the same model making two narrow structured decisions. This is a small-model result; a frontier model would likely close much of the gap.
- **Latency includes GPU queueing** (32 runs in flight against one server). H7's effect (0.83 s) is real but its CI is wide; mock tool latency was 0.25 s per call and 2 s per timeout.
- **One synthetic job, one model.** 60 generated tasks from one domain, mocks rather than real APIs, Qwen3-8B only.
- **Run integrity.** The confirmatory run was interrupted twice (Colab reclaimed the VM; two accidental double-driver starts were discarded before any outcomes were viewed). The final file has 3,780 unique runs from single drivers: 2,231 rows from one driver, then 1,549 resumed rows on a new VM with vLLM 0.31.0 and the structured-output backend named explicitly (`xgrammar`). No-fault success by block: first 2,231 rows V2-V7 90-94%, resumed rows 90-97%; V1 56% vs 58%. Full log in `results/incident_double_driver.md`.

## Timing

Estimated 165 min, actual about 230 min (setup with GPU allocation waits 65, pilot 20, confirmatory GPU run 135 wall clock including two VM losses, eval 5, writeup 25). GPU: NVIDIA L4 on Colab (three VMs in sequence). Compute: about 4.8 CU (account balance 131.81 to 127.05). The final resumed driver ran 1,549 runs in 664 s.
