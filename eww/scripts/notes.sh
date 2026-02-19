#!/bin/bash
# Read last 8 lines of notes file as JSON for the dashboard

NOTES_FILE="$HOME/.local/share/dashboard/notes.md"

if [ ! -f "$NOTES_FILE" ]; then
    echo '{"content":"Sem notas ainda.","empty":true}'
    exit 0
fi

CONTENT=$(tail -n 8 "$NOTES_FILE" 2>/dev/null)

if [ -z "$CONTENT" ]; then
    echo '{"content":"Sem notas ainda.","empty":true}'
    exit 0
fi

# Escape for JSON: backslashes, quotes, newlines, tabs
ESCAPED=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")

echo "{\"content\":${ESCAPED},\"empty\":false}"
