#!/home/vvaxis/Projects/dashboard/eww/scripts/.venv/bin/python3
"""Fetch Google Calendar events for a given date."""

import json
import sys
import os
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CONFIG_DIR = os.path.expanduser("~/.config/dashboard")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "google-credentials.json")
TOKEN_FILE = os.path.join(CONFIG_DIR, "google-token.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

DAYS_PT = {
    "Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta",
    "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo"
}

MONTHS_PT = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
}


def get_date_label(date):
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    if date == today:
        return "Hoje"
    elif date == tomorrow:
        return "Amanhã"
    else:
        day_name = DAYS_PT.get(date.strftime("%A"), date.strftime("%A"))
        return f"{day_name}, {date.day} {MONTHS_PT[date.month]}"


def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def fetch_events(date_str):
    date = datetime.date.fromisoformat(date_str)
    date_label = get_date_label(date)

    creds = authenticate()
    if not creds:
        return {
            "date": date_str,
            "dateLabel": date_label,
            "events": [],
            "count": 0,
            "error": "Configurar credenciais"
        }

    service = build("calendar", "v3", credentials=creds)

    # Timezone local
    try:
        tz = datetime.datetime.now().astimezone().tzinfo
    except Exception:
        tz = None

    if tz:
        start = datetime.datetime.combine(date, datetime.time.min, tzinfo=tz).isoformat()
        end = datetime.datetime.combine(date, datetime.time.max, tzinfo=tz).isoformat()
    else:
        start = datetime.datetime.combine(date, datetime.time.min).isoformat() + "Z"
        end = datetime.datetime.combine(date, datetime.time.max).isoformat() + "Z"

    # Busca todos os calendários do usuário
    calendars = service.calendarList().list().execute()
    all_events = []

    for cal in calendars.get("items", []):
        cal_id = cal["id"]
        try:
            result = service.events().list(
                calendarId=cal_id,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
        except Exception:
            continue

        for item in result.get("items", []):
            start_info = item.get("start", {})
            if "dateTime" in start_info:
                t = datetime.datetime.fromisoformat(start_info["dateTime"])
                time_str = t.strftime("%H:%M")
                sort_key = t
            else:
                time_str = "dia todo"
                sort_key = datetime.datetime.combine(date, datetime.time.min)

            all_events.append({
                "time": time_str,
                "title": item.get("summary", "(sem título)"),
                "_sort": sort_key
            })

    # Ordena por horário e remove chave auxiliar
    all_events.sort(key=lambda e: e["_sort"])
    events = [{"time": e["time"], "title": e["title"]} for e in all_events]

    return {
        "date": date_str,
        "dateLabel": date_label,
        "events": events,
        "count": len(events)
    }


def main():
    if len(sys.argv) < 2:
        date_str = datetime.date.today().isoformat()
    else:
        date_str = sys.argv[1]

    data = fetch_events(date_str)
    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "date": sys.argv[1] if len(sys.argv) > 1 else "",
            "dateLabel": "",
            "events": [],
            "count": 0,
            "error": str(e)
        }))
