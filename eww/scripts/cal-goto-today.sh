#!/bin/bash
# Reset calendar to current month and fetch today's events

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
EWW_DIR="$(dirname "$SCRIPTS_DIR")"
CACHE_DIR="/tmp/dashboard-cache"

NEW_DATA=$("$SCRIPTS_DIR/cal-data.py")

# Usar cache se disponível
TODAY=$(date +%Y-%m-%d)
mkdir -p "$CACHE_DIR"
CACHE_FILE="$CACHE_DIR/events-$TODAY.json"
EVENTS='{"date":"","dateLabel":"Hoje","events":[],"count":0}'
if [ -f "$CACHE_FILE" ] && [ $(($(date +%s) - $(stat -c %Y "$CACHE_FILE"))) -lt 300 ]; then
    EVENTS=$(cat "$CACHE_FILE")
fi

eww -c "$EWW_DIR" update cal-data="$NEW_DATA" cal-selected-day=0 events-data="$EVENTS"

# Refresh em background com request ID
REQUEST_ID="$$-$(date +%s%N)"
printf '%s' "$REQUEST_ID" > /tmp/dashboard-events-request
(
    TMPFILE=$(mktemp /tmp/dashboard-events.XXXXXX)
    "$SCRIPTS_DIR/gcal-events.py" "$TODAY" > "$TMPFILE" 2>/tmp/dashboard-events.log
    FRESH=$(cat "$TMPFILE")
    rm -f "$TMPFILE"
    CURRENT=$(cat /tmp/dashboard-events-request 2>/dev/null)
    if [ "$REQUEST_ID" = "$CURRENT" ] && [ -n "$FRESH" ]; then
        printf '%s' "$FRESH" > "$CACHE_FILE"
        eww -c "$EWW_DIR" update events-data="$FRESH"
    fi
) &
