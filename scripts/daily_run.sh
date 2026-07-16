#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/daily_run_$TS.log"

{
  echo "=== daily run started $(date) ==="
  cd "$PROJECT_DIR"

  echo "--- ingestion ---"
  python3 ingestion/run.py

  echo "--- reasoning (limit 20) ---"
  python3 reasoning/run.py --limit 20

  echo "=== daily run finished $(date) ==="
} >> "$LOG_FILE" 2>&1

# keep only the last 30 log files
ls -t "$LOG_DIR"/daily_run_*.log 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true
