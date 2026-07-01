#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$SCRIPT_DIR/.venv/bin/python"
LOG="$SCRIPT_DIR/briefings/run-log.txt"

# Load API keys from .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

echo "" >> "$LOG"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"

cd "$REPO_DIR"

echo "[Anthropic] starting..." >> "$LOG"
if "$PYTHON" "$SCRIPT_DIR/anthropic_agent.py" >> "$LOG" 2>&1; then
    echo "[Anthropic] OK" >> "$LOG"
else
    echo "[Anthropic] FAILED (exit $?)" >> "$LOG"
fi

echo "[OpenAI] starting..." >> "$LOG"
if "$PYTHON" "$SCRIPT_DIR/openai_agent.py" >> "$LOG" 2>&1; then
    echo "[OpenAI] OK" >> "$LOG"
else
    echo "[OpenAI] FAILED (exit $?)" >> "$LOG"
fi

echo "=== done ===" >> "$LOG"
