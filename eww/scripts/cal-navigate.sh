#!/bin/bash
# Navigate calendar months: cal-navigate.sh <next|prev>

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
EWW_DIR="$(dirname "$SCRIPTS_DIR")"

# Get current displayed month/year from eww using python to parse JSON
CAL_JSON=$(eww -c "$EWW_DIR" get cal-data)
read -r MONTH YEAR <<< "$(printf '%s' "$CAL_JSON" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print(d['monthNum'], d['year'])
")"

if [ "$1" = "next" ]; then
    MONTH=$((MONTH + 1))
    if [ "$MONTH" -gt 12 ]; then
        MONTH=1
        YEAR=$((YEAR + 1))
    fi
elif [ "$1" = "prev" ]; then
    MONTH=$((MONTH - 1))
    if [ "$MONTH" -lt 1 ]; then
        MONTH=12
        YEAR=$((YEAR - 1))
    fi
fi

# Update calendar data, clear selection and events
NEW_DATA=$("$SCRIPTS_DIR/cal-data.py" "$YEAR" "$MONTH")
eww -c "$EWW_DIR" update cal-data="$NEW_DATA" cal-selected-day=0 events-data='{"date":"","dateLabel":"","events":[],"count":0}'
