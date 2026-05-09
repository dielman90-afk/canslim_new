#!/bin/bash
# Taeglicher CANSLIM-Analyse-Runner fuer Claude Code
# Wird von cron Mo-Fr um 09:10 aufgerufen

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$REPO_DIR/canslim_cron.log"
PROMPT_FILE="$REPO_DIR/run_canslim.md"

echo "" >> "$LOG_FILE"
echo "===== $(date '+%Y-%m-%d %H:%M:%S') =====" >> "$LOG_FILE"

cd "$REPO_DIR" || exit 1

claude --print "$(cat "$PROMPT_FILE") -- Heutiges Datum: $(date '+%Y-%m-%d')" \
  >> "$LOG_FILE" 2>&1

echo "Exit-Code: $?" >> "$LOG_FILE"
