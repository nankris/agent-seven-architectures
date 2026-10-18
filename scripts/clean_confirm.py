"""Remove rows possibly contaminated by the accidental second driver (see results/incident_double_driver.md).
Keeps lines 1-1247 and 2067+, then de-duplicates keys (first wins). Dropped rows go to runs_confirm_dropped.jsonl;
run_phase.py then re-runs the missing jobs with a single driver.
  python clean_confirm.py results/runs_confirm.jsonl
"""
import json, sys
p = sys.argv[1]
lines = open(p).read().splitlines()
keep, drop, seen = [], [], set()
for i, l in enumerate(lines, 1):
    r = json.loads(l)
    k = (r["arch"], r["task"], r["seed"], r["condition"])
    if 1247 < i <= 2066 or k in seen:
        drop.append(l)
    else:
        keep.append(l); seen.add(k)
open(p.replace(".jsonl", "_dropped.jsonl"), "w").write("\n".join(drop) + "\n")
open(p, "w").write("\n".join(keep) + "\n")
print(f"kept {len(keep)}, dropped {len(drop)}")
