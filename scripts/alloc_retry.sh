#!/bin/bash
# Retry L4 allocation every 5 min for up to 2 h (account allows 2 concurrent GPU sessions).
source "${COLAB_SETUP:-$HOME/colab-tools/setup.sh}" >/dev/null 2>&1
for i in $(seq 1 24); do
  if colab sessions 2>&1 | grep -q agents-l4; then echo "$(date) session exists"; exit 0; fi
  echo "$(date) attempt $i"; colab new --gpu L4 -s agents-l4 2>&1 | tail -2
  colab sessions 2>&1 | grep -q agents-l4 && { echo "$(date) allocated"; exit 0; }
  sleep 300
done
