#!/bin/bash
# Stream de status do player via playerctl --follow
# Output: uma linha JSON por mudança de estado

json_line() {
    local title="$1" artist="$2" status="$3"
    # Escapa aspas e backslashes para JSON válido
    title="${title//\\/\\\\}"
    title="${title//\"/\\\"}"
    artist="${artist//\\/\\\\}"
    artist="${artist//\"/\\\"}"
    echo "{\"title\":\"$title\",\"artist\":\"$artist\",\"status\":\"$status\"}"
}

# Estado inicial
if playerctl status &>/dev/null; then
    title=$(playerctl metadata title 2>/dev/null)
    artist=$(playerctl metadata artist 2>/dev/null)
    status=$(playerctl status 2>/dev/null)
    json_line "$title" "$artist" "$status"
else
    json_line "" "" "Stopped"
fi

# Stream contínuo — tab-separated para evitar problemas com JSON
playerctl metadata --follow --format $'{{status}}\t{{artist}}\t{{title}}' 2>/dev/null | while IFS=$'\t' read -r status artist title; do
    json_line "$title" "$artist" "$status"
done
