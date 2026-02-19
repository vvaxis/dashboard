#!/bin/bash
# Fecha o dashboard e mata o daemon se estiver rodando

EWW_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if eww -c "$EWW_DIR" ping &>/dev/null; then
    eww -c "$EWW_DIR" close dashboard-left dashboard-right
    eww -c "$EWW_DIR" kill
fi
