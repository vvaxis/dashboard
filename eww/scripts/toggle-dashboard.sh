#!/bin/bash
# Toggle do dashboard eww (split-panel HUD)

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
EWW_DIR="$(dirname "$SCRIPTS_DIR")"
CACHE_DIR="/tmp/dashboard-cache"

STATE=$(eww -c "$EWW_DIR" get dashboard-open)

if [ "$STATE" = "true" ]; then
    eww -c "$EWW_DIR" close dashboard-left dashboard-right
    eww -c "$EWW_DIR" update dashboard-open=false
else
    # Calendar data é rápido (~50ms)
    CAL_DATA=$("$SCRIPTS_DIR/cal-data.py")

    # Usar cache de eventos se existir (< 5 min), senão vazio
    mkdir -p "$CACHE_DIR"
    TODAY=$(date +%Y-%m-%d)
    CACHE_FILE="$CACHE_DIR/events-$TODAY.json"
    EVENTS='{"date":"","dateLabel":"Hoje","events":[],"count":0}'
    if [ -f "$CACHE_FILE" ] && [ $(($(date +%s) - $(stat -c %Y "$CACHE_FILE"))) -lt 300 ]; then
        EVENTS=$(cat "$CACHE_FILE")
    fi

    # Abrir IMEDIATAMENTE com dados disponíveis
    eww -c "$EWW_DIR" update dashboard-open=true cal-data="$CAL_DATA" cal-selected-day=0 events-data="$EVENTS"
    eww -c "$EWW_DIR" open dashboard-left
    eww -c "$EWW_DIR" open dashboard-right

    # Buscar eventos frescos em background com request ID
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
fi
