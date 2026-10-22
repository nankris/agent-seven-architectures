"""Run every (arch, task, seed, condition) for one phase; resumable (skips rows already in the JSONL).

  python run_phase.py --phase pilot   --seeds 0        --out runs_pilot.jsonl
  python run_phase.py --phase confirm --seeds 0 1 2    --out runs_confirm.jsonl
  STUB=1 python run_phase.py ...     # scripted fake model, for plumbing tests without a GPU
"""
import argparse
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agents as A

ap = argparse.ArgumentParser()
ap.add_argument("--phase", choices=["pilot", "confirm"], required=True)
ap.add_argument("--seeds", type=int, nargs="+", default=[0])
ap.add_argument("--conditions", nargs="+", default=["clean", "timeout", "crash"])
ap.add_argument("--archs", nargs="+", default=A.ARCHS)
ap.add_argument("--tasks", default=str(Path(__file__).resolve().parents[1] / "results" / "tasks.json"))
ap.add_argument("--out", required=True)
ap.add_argument("--workers", type=int, default=24)
ap.add_argument("--limit", type=int, default=0)
args = ap.parse_args()

data = json.load(open(args.tasks))
policy = data["policy"]
pref = "P" if args.phase == "pilot" else "T"
tasks = [t for t in data["tasks"] if t["id"].startswith(pref)]
if args.limit:
    tasks = tasks[:args.limit]

done = set()
if os.path.exists(args.out):
    for line in open(args.out):
        try:
            r = json.loads(line)
            done.add((r["arch"], r["task"], r["seed"], r["condition"]))
        except Exception:
            pass

jobs = [(a, t, s, c) for s in args.seeds for t in tasks for c in args.conditions for a in args.archs
        if (a, t["id"], s, c) not in done]
random.Random(7).shuffle(jobs)   # mix archs so GPU load and any drift are spread evenly
print(f"{len(done)} done, {len(jobs)} to run", flush=True)

factory = None
if os.environ.get("STUB"):
    from stub_llm import StubLLM
    factory = lambda u, sd: StubLLM(u, sd)

lock = threading.Lock()
t0 = time.time()


def work(j):
    a, t, s, c = j
    try:
        return A.run_one(a, t, policy, s, c, llm_factory=factory)
    except BaseException as e:   # never let one run kill the driver
        return {"arch": a, "task": t["id"], "seed": s, "condition": c, "harness_error": repr(e)[:300]}


n = 0
with ThreadPoolExecutor(args.workers) as ex:
    futs = [ex.submit(work, j) for j in jobs]
    for fu in as_completed(futs):
        r = fu.result()
        if "harness_error" in r:
            print("HARNESS ERROR", r, flush=True)
            continue
        with lock:
            with open(args.out, "a") as fh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        n += 1
        if n % 25 == 0 or n == len(jobs):
            print(f"[{time.strftime('%H:%M:%S')}] {n}/{len(jobs)} rows  elapsed {time.time() - t0:.0f}s", flush=True)
print("PHASE DONE", args.phase, f"{time.time() - t0:.0f}s", flush=True)
