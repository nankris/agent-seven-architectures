#!/bin/bash
# Local side: copy the confirmatory JSONL + log off the VM every 3 min until the driver exits.
source "${COLAB_SETUP:-$HOME/colab-tools/setup.sh}" >/dev/null 2>&1
cd "$(dirname "$0")/.."
for i in $(seq 1 40); do
  timeout 120 colab download -s agents-l4 /content/agents/run_confirm.log results/run_confirm.log >/dev/null 2>&1
  timeout 120 colab download -s agents-l4 /content/agents/results/runs_confirm.jsonl results/runs_confirm.tmp >/dev/null 2>&1 && \
    [ $(wc -l < results/runs_confirm.tmp) -ge $(cat results/runs_confirm.jsonl 2>/dev/null | wc -l) ] && mv results/runs_confirm.tmp results/runs_confirm.jsonl
  echo "$(date -u +%H:%M) $(wc -l < results/runs_confirm.jsonl 2>/dev/null) rows; $(tail -1 results/run_confirm.log 2>/dev/null)"
  grep -q EXIT results/run_confirm.log 2>/dev/null && break
  sleep 180
done
