#!/bin/bash
# Runs ON the Colab VM: kill the pilot driver + vLLM, restart vLLM with the vm_setup.sh flags (no reinstall).
cd /content/agents
pkill -f run_phase.py; pkill -f "vllm.entrypoints"; sleep 15
exec > restart.log 2>&1
date
eval "$(sed -n '/^setsid nohup python -m vllm/,/< \/dev\/null &$/p' scripts/vm_setup.sh)"
for i in $(seq 1 90); do curl -s 127.0.0.1:8000/v1/models >/dev/null && { date; echo VLLM_READY; break; }; sleep 10; done
