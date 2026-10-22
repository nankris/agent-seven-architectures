#!/bin/bash
# Runs ON the Colab VM, detached: one phase of runs, resumable (skips rows already in the JSONL).
cd /content/agents
PHASE=$1; shift
export CKPT_DIR=/content/agents/ckpt
python scripts/run_phase.py --phase $PHASE --out results/runs_$PHASE.jsonl --workers ${WORKERS:-24} "$@" >> run_$PHASE.log 2>&1
echo "EXIT $?" >> run_$PHASE.log
