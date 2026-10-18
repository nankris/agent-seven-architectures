# I broke the same AI agent seven ways. Only one thing stopped it paying twice.

Brahim Guaali wrote a lovely piece called [I rebuilt one AI agent seven times to understand graph engineering](https://medium.com/@brahimg/i-rebuilt-one-ai-agent-seven-times-to-understand-graph-engineering-80b9983cd921). He takes a food-delivery refund agent and rebuilds it step by step: a plain ReAct loop, then structured state, parallel nodes, checkpointing, human approval, retries, and finally all of it together. His [code is on GitHub](https://github.com/brahim-guaali/graph-engineering-from-first-principles).

His demos show what each layer is for. I wanted numbers. So I rebuilt his seven agents on an open model, gave them real side effects, and then broke every one of them at exactly the same moments.

## The setup

The agent reads a customer message and has to do exactly the right things: look up the order, the policy and a fraud score, then issue the right refund, maybe a $5 credit, maybe a ticket, and email the customer. Refunds over $500 need a manager's approval. The "send money" tools are mocks that write to a ledger, so I can count every refund that actually went out.

The model is Qwen3-8B, served with vLLM on a single Colab L4 GPU. All seven versions are LangGraph graphs.

Each version ran 60 fresh tasks, 3 seeds each, under three conditions:

- **No fault.**
- **API timeout.** The fraud lookup hangs and fails. Then the first refund *goes through* but the acknowledgement is lost, so the agent thinks it failed. That is the nasty real-world case.
- **Crash.** The first refund goes through, then the process dies. A new process picks the job back up.

That is 3,780 runs in total. Before running anything I wrote down eight predictions taken from the source article, with margins and a fixed rule: a prediction is PROVEN only if the whole 95% confidence interval clears the margin.

## Result 1: checkpointing does not stop double payments

This is the one that matters (figures/fig1_duplicates.png).

When something failed, the plain ReAct loop sent a refund, credit or ticket twice in **63%** of runs. The full graph did it in **0%**.

But look at which layer gets you there. Structured state: 97% duplicates. Parallel nodes: 97%. Human approval: 97%. **Checkpointing: 100%.**

That last one surprises people. Checkpointing saves your progress after each step. But the crash happened *after* the refund went out and *before* the step was saved. So on resume, the graph honestly believes the refund step never finished, and it runs it again. Every single time.

The two versions with 0% duplicates are the two that put an **idempotency key** on every side effect: a key built from the run id and the step name. The second attempt to refund shows up with the same key, the ledger says "already done", and nothing is paid twice. Over all faulted runs, those keys caught about 360 repeat attempts per architecture.

In money terms, across the faulted runs the loop overpaid customers by about $71,000, and checkpointing alone by about $37,000. The two keyed versions overpaid about $1,500, and that was from the model picking a wrong amount, not from duplicates.

If you take one thing from this post: **retries and resumes are only safe when every side effect is idempotent.** Checkpointing is about not redoing work. It is not about not redoing damage.

## Result 2: the graph is much cheaper

On runs with no fault (figures/fig3_cost.png):

- The loop made **5.4** model calls per task. The structured graph made **1.9**. That is a 65% cut. The source predicted 41%.
- Prompt tokens fell from **6,752** to **635**, a 91% cut. The source predicted 78%.

Why so large? In a loop, every call re-reads the whole growing transcript of tool calls and results. In the graph, code does the lookups and the routing, and the model is asked two narrow questions: "what kind of complaint is this?" and "what should we do?". Each sees a small, clean prompt.

Checkpointing also earned its keep in a different way. After a crash, the checkpointed versions resumed with zero extra model calls. The versions without checkpoints started over and paid 1.9 extra calls per crash. Running the three lookups in parallel saved 0.83 seconds per task.

## Result 3: my "it's a tie" prediction was wrong

The source found that the loop and the graph were equally accurate when nothing failed: 12 out of 12 each, on Gemini. I pre-registered that as a tie, within 10 points either way.

It was not a tie (figures/fig2_success.png). With no faults at all, the loop got **57%** of tasks fully right. The full graph got **92%**. The gap is 35 points, with a confidence interval of 21 to 48. Prediction disproven.

The loop fell apart on the fiddly cases. Cancelled orders: 3 of 18 right. Rider and app complaints: 0 of 18. Messages with a prompt-injection attempt: 0 of 18. Usually the amount was wrong, a credit was skipped, or the customer was never emailed.

My honest read: an 8B model is fine at two narrow, structured decisions and bad at running a ten-step procedure by itself. A frontier model would probably close a lot of that gap. But if you run small open models, structure is not just a cost saving. It is the difference between working and not.

## Result 4: timeouts derail loops in a different way

The plain loop got **0%** of tasks right under the timeout. The full graph got **92%**.

What surprised me is *how* the loop failed. Only 30% of its timeout runs paid twice. The rest simply went off-script. When the fraud lookup errored, the model would often open a support ticket and stop, or skip the credit. Nobody told it to do that. An error message in the transcript was enough to push it off the happy path.

So "will my agent retry badly?" is only half the question. The other half is "will an error make it forget the job?"

## Scorecard

Seven of my eight predictions held. The one that missed was the accuracy tie (figures/table.png). The full per-architecture numbers are in figures/table_archs.png.

## Caveats

- **My faults suit idempotency keys.** The mock ledger honours keys perfectly. With a real payment API, the key has to be sent to the provider. A key that only lives in your own process cannot stop a duplicate on their side.
- **The versions without retries restart from scratch after any error.** That is a choice I fixed in advance, and it is what drives their 97% duplicate rate. A runner that gave up on the first error would duplicate less and finish less.
- **One job, one model, mocks.** 60 synthetic tasks from one domain, Qwen3-8B only.
- **Latency includes GPU queueing**, since 32 runs shared one server.
- **The run was messy.** Colab took my GPU away twice mid-run. I resumed from saved results, with one change: a newer vLLM needed a server flag spelled differently. Results before and after the resume look the same. The incident log is in the repo.

## The takeaway

Graphs make small-model agents cheaper and far more reliable. But the property that stops an agent from paying twice is boring: give every side effect a stable key and let the receiving system refuse repeats. Checkpointing without that key did nothing to stop double payments.

*Timing: estimated 165 minutes, actual about 230. One Colab L4 GPU, about 4.8 compute units.*
