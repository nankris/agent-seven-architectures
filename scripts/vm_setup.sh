#!/bin/bash
# Runs ON the Colab VM (launched detached). Installs vLLM + LangGraph, starts the Qwen3-8B server.
cd /content/agents
exec > setup.log 2>&1
date; nvidia-smi
pip install -q "vllm>=0.10" "langgraph>=1.0,<1.2" "langgraph-checkpoint-sqlite>=2.0" 2>&1 | tail -3
python -c "import vllm, langgraph; print('vllm', vllm.__version__)"
pip list 2>/dev/null | grep -iE "^(vllm|langgraph|langgraph-checkpoint-sqlite|openai|torch|transformers) "
date; echo "starting vllm"
setsid nohup python -m vllm.entrypoints.openai.api_server --model ${MODEL:-Qwen/Qwen3-8B-FP8} \
  --served-model-name Qwen/Qwen3-8B --host 127.0.0.1 --port 8000 --max-model-len 8192 \
  --gpu-memory-utilization 0.90 --enable-auto-tool-choice --tool-call-parser hermes \
  --enable-prefix-caching --max-num-seqs 48 --seed 0 \
  --structured-outputs-config '{"backend": "xgrammar", "disable_any_whitespace": true}' > vllm.log 2>&1 < /dev/null &
for i in $(seq 1 120); do curl -s 127.0.0.1:8000/v1/models >/dev/null && { date; echo VLLM_READY; break; }; sleep 10; done
