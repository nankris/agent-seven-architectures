"""Pre-registered analysis for Exp 133. Unit = task (mean over seeds), paired across archs.
95% percentile bootstrap over tasks, 10,000 resamples, seed 0.

  python analyze.py results/runs_confirm.jsonl results/summary.json
"""
import json
import sys
from collections import defaultdict

import numpy as np

src = sys.argv[1] if len(sys.argv) > 1 else "results/runs_confirm.jsonl"
dst = sys.argv[2] if len(sys.argv) > 2 else "results/summary.json"
rows = [json.loads(l) for l in open(src)]
ARCHS = ["V1_react", "V2_structured", "V3_parallel", "V4_checkpoint", "V5_approval", "V6_retries", "V7_full"]
CONDS = ["clean", "timeout", "crash"]
tasks = sorted({r["task"] for r in rows})
B, RNG = 10000, np.random.default_rng(0)
IDX = RNG.integers(0, len(tasks), size=(B, len(tasks)))


def per_task(metric, arch, conds):
    """task -> mean over seeds (and pooled conditions) of metric."""
    d = defaultdict(list)
    for r in rows:
        if r["arch"] == arch and r["condition"] in conds:
            d[r["task"]].append(float(metric(r)))
    return np.array([np.mean(d[t]) for t in tasks])


def ci(x):
    bs = x[IDX].mean(1)
    return float(x.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def ci_ratio(a, b):
    """relative reduction 1 - mean(b)/mean(a), bootstrapped over paired tasks."""
    bs = 1 - b[IDX].mean(1) / a[IDX].mean(1)
    return float(1 - b.mean() / a.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def verdict(est, lo, hi, margin, direction=+1):
    """PROVEN if the whole CI is beyond the margin in the predicted direction; DISPROVEN if wholly on the other side."""
    lo, hi = (lo, hi) if direction > 0 else (-hi, -lo)
    if lo > margin: return "PROVEN"
    if hi < margin: return "DISPROVEN"
    return "INCONCLUSIVE"


M = {"success": lambda r: r["success"], "dup": lambda r: r["any_dup_money"], "calls": lambda r: r["model_calls"],
     "ptok": lambda r: r["prompt_tokens"], "ctok": lambda r: r["completion_tokens"], "lat": lambda r: r["latency_s"],
     "dupn": lambda r: r["dup_notify"], "restarts": lambda r: r["restarts"], "overpaid": lambda r: r["overpaid"]}

table = []
for a in ARCHS:
    for c in CONDS + ["faulted"]:
        cs = ["timeout", "crash"] if c == "faulted" else [c]
        row = {"arch": a, "condition": c, "n_runs": sum(1 for r in rows if r["arch"] == a and r["condition"] in cs)}
        for k, f in M.items():
            m, lo, hi = ci(per_task(f, a, cs))
            row[k] = m; row[k + "_lo"] = lo; row[k + "_hi"] = hi
        table.append(row)

H = {}
# H1: dup rate V1 - V7, faulted pooled, margin 5 pp
x = per_task(M["dup"], "V1_react", ["timeout", "crash"]) - per_task(M["dup"], "V7_full", ["timeout", "crash"])
e = ci(x); H["H1"] = dict(metric="any_dup_money V1-V7 faulted (pp)", est=e[0] * 100, lo=e[1] * 100, hi=e[2] * 100,
                          margin=5, verdict=verdict(*[v * 100 for v in e], 5))
# H2: relative reduction in model calls V1 -> V2, clean, margin 25%
e = ci_ratio(per_task(M["calls"], "V1_react", ["clean"]), per_task(M["calls"], "V2_structured", ["clean"]))
H["H2"] = dict(metric="model-call reduction V1->V2 clean (%)", est=e[0] * 100, lo=e[1] * 100, hi=e[2] * 100,
               margin=25, verdict=verdict(*[v * 100 for v in e], 25))
# H3: prompt tokens reduction, margin 50%
e = ci_ratio(per_task(M["ptok"], "V1_react", ["clean"]), per_task(M["ptok"], "V2_structured", ["clean"]))
H["H3"] = dict(metric="prompt-token reduction V1->V2 clean (%)", est=e[0] * 100, lo=e[1] * 100, hi=e[2] * 100,
               margin=50, verdict=verdict(*[v * 100 for v in e], 50))
# H4: extra model calls after crash, V3 minus V4, margin 1 call
ex3 = per_task(M["calls"], "V3_parallel", ["crash"]) - per_task(M["calls"], "V3_parallel", ["clean"])
ex4 = per_task(M["calls"], "V4_checkpoint", ["crash"]) - per_task(M["calls"], "V4_checkpoint", ["clean"])
e = ci(ex3 - ex4); H["H4"] = dict(metric="extra calls after crash, V3 minus V4", est=e[0], lo=e[1], hi=e[2], margin=1,
                                  verdict=verdict(*e, 1), v3_extra=float(ex3.mean()), v4_extra=float(ex4.mean()))
# H5: V4 crash dup rate, CI lower bound > 50% = PROVEN; upper < 50% = DISPROVEN
e = ci(per_task(M["dup"], "V4_checkpoint", ["crash"]))
H["H5"] = dict(metric="any_dup_money V4 crash (%)", est=e[0] * 100, lo=e[1] * 100, hi=e[2] * 100, margin=50,
               verdict=verdict(*[v * 100 for v in e], 50))
# H6: equivalence, success V7 - V1 clean within +-10 pp
x = per_task(M["success"], "V7_full", ["clean"]) - per_task(M["success"], "V1_react", ["clean"])
e = [v * 100 for v in ci(x)]
v = "PROVEN" if (e[1] > -10 and e[2] < 10) else ("DISPROVEN" if (e[1] > 10 or e[2] < -10) else "INCONCLUSIVE")
H["H6"] = dict(metric="success V7-V1 clean (pp), equivalence +-10", est=e[0], lo=e[1], hi=e[2], margin=10, verdict=v)
# H7: latency V2 - V3 clean, margin 0.25 s
e = ci(per_task(M["lat"], "V2_structured", ["clean"]) - per_task(M["lat"], "V3_parallel", ["clean"]))
H["H7"] = dict(metric="latency V2-V3 clean (s)", est=e[0], lo=e[1], hi=e[2], margin=0.25, verdict=verdict(*e, 0.25))
# H8: success V7 - V1 timeout, margin 10 pp
x = per_task(M["success"], "V7_full", ["timeout"]) - per_task(M["success"], "V1_react", ["timeout"])
e = [v * 100 for v in ci(x)]
H["H8"] = dict(metric="success V7-V1 timeout (pp)", est=e[0], lo=e[1], hi=e[2], margin=10, verdict=verdict(*e, 10))

# fault firing sanity
fired = defaultdict(lambda: [0, 0])
for r in rows:
    if r["condition"] != "clean":
        k = (r["arch"], r["condition"])
        fired[k][1] += 1
        fired[k][0] += int(r["fault_fired"]["crash"] if r["condition"] == "crash" else
                           (r["fault_fired"]["money_timeout"] or r["fault_fired"]["fraud_timeout"]))
out = {"source": src, "n_rows": len(rows), "n_tasks": len(tasks), "seeds": sorted({r["seed"] for r in rows}),
       "hypotheses": H, "table": table,
       "fault_fired": {f"{a}|{c}": v for (a, c), v in fired.items()},
       "tokens_total": {"prompt": sum(r["prompt_tokens"] for r in rows), "completion": sum(r["completion_tokens"] for r in rows),
                        "model_calls": sum(r["model_calls"] for r in rows)}}
json.dump(out, open(dst, "w"), indent=1)
for k, h in H.items():
    print(f"{k}: {h['metric']}: {h['est']:.2f} [{h['lo']:.2f}, {h['hi']:.2f}] margin {h['margin']} -> {h['verdict']}")
print(f"{'arch':15s} {'cond':8s} succ  dup  calls  ptok   lat")
for r in table:
    print(f"{r['arch']:15s} {r['condition']:8s} {r['success']:.2f} {r['dup']:.2f} {r['calls']:5.2f} {r['ptok']:6.0f} {r['lat']:5.2f}")
