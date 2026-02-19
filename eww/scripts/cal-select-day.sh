#!/bin/bash
# Select a day in the calendar and fetch events: cal-select-day.sh <day>

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
EWW_DIR="$(dirname "$SCRIPTS_DIR")"
CACHE_DIR="/tmp/dashboard-cache"

DAY="$1"
REQUEST_ID="$$-$(date +%s%N)"
printf '%s' "$REQUEST_ID" > /tmp/dashboard-events-request

# Seleção visual IMEDIATA
eww -c "$EWW_DIR" update cal-selected-day="$DAY"

# Build full date from calendar state (pipe JSON via stdin para evitar quoting)
CAL_JSON=$(eww -c "$EWW_DIR" get cal-data)
read -r MONTH YEAR <<< "$(printf '%s' "$CAL_JSON" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print(d['monthNum'], d['year'])
")"

FULL_DATE=$(printf "%04d-%02d-%02d" "$YEAR" "$MONTH" "$DAY")
mkdir -p "$CACHE_DIR"
CACHE_FILE="$CACHE_DIR/events-$FULL_DATE.json"

# Se tem cache recente (< 5 min), mostra imediatamente enquanto o fetch roda
if [ -f "$CACHE_FILE" ] && [ $(($(date +%s) - $(stat -c %Y "$CACHE_FILE"))) -lt 300 ]; then
    CACHED=$(cat "$CACHE_FILE")
    [ -n "$CACHED" ] && eww -c "$EWW_DIR" update events-data="$CACHED"
fi

# Fetch eventos frescos em background com validação de request ID
(
    TMPFILE=$(mktemp /tmp/dashboard-events.XXXXXX)
    "$SCRIPTS_DIR/gcal-events.py" "$FULL_DATE" > "$TMPFILE" 2>/tmp/dashboard-events.log
    EVENTS=$(cat "$TMPFILE")
    rm -f "$TMPFILE"
    CURRENT=$(cat /tmp/dashboard-events-request 2>/dev/null)
    if [ "$REQUEST_ID" = "$CURRENT" ] && [ -n "$EVENTS" ]; then
        printf '%s' "$EVENTS" > "$CACHE_FILE"
        eww -c "$EWW_DIR" update events-data="$EVENTS"
    fi
) &
