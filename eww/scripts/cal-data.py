#!/usr/bin/env python3
"""Gera JSON do calendário mensal para o dashboard eww."""

import json
import calendar
import datetime
import sys

MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

def main():
    today = datetime.date.today()

    # Accept optional year month arguments
    if len(sys.argv) == 3:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        year = today.year
        month = today.month

    # Domingo como primeiro dia da semana
    cal = calendar.Calendar(firstweekday=6)
    weeks = []
    for week in cal.monthdayscalendar(year, month):
        weeks.append(week)

    # today field: only set when viewing the current month
    today_day = today.day if (year == today.year and month == today.month) else 0

    data = {
        "month": MESES[month],
        "year": year,
        "monthNum": month,
        "currentMonth": today.month,
        "currentYear": today.year,
        "today": today_day,
        "weeks": weeks
    }

    print(json.dumps(data))

if __name__ == "__main__":
    main()
