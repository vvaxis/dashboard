#!/usr/bin/env python3
"""Fetch weather data from OpenWeatherMap for the dashboard."""

import json
import urllib.request
import urllib.error
import datetime
import os

CONFIG_DIR = os.path.expanduser("~/.config/dashboard")

# OWM condition code → Nerd Font weather icon (day variants)
ICONS_DAY = {
    200: "\ue30f", 201: "\ue30f", 202: "\ue30f",
    210: "\ue305", 211: "\ue305", 212: "\ue305", 221: "\ue305",
    230: "\ue30f", 231: "\ue30f", 232: "\ue30f",
    300: "\ue30b", 301: "\ue30b", 302: "\ue308",
    310: "\ue308", 311: "\ue308", 312: "\ue308",
    313: "\ue308", 314: "\ue308", 321: "\ue30b",
    500: "\ue30b", 501: "\ue308", 502: "\ue308", 503: "\ue308", 504: "\ue308",
    511: "\ue306", 520: "\ue309", 521: "\ue309", 522: "\ue309", 531: "\ue30e",
    600: "\ue30a", 601: "\ue30a", 602: "\ue30a",
    611: "\ue306", 612: "\ue306", 613: "\ue306",
    615: "\ue306", 616: "\ue306", 620: "\ue306", 621: "\ue30a", 622: "\ue30a",
    701: "\ue313", 711: "\ue35c", 721: "\ue3ae", 731: "\ue35d",
    741: "\ue303", 751: "\ue35d", 761: "\ue35d", 762: "\ue35d",
    771: "\ue300", 781: "\ue351",
    800: "\ue30d",
    801: "\ue300", 802: "\ue300", 803: "\ue300", 804: "\ue30c",
}

# OWM condition code → Nerd Font weather icon (night variants)
ICONS_NIGHT = {
    200: "\ue338", 201: "\ue338", 202: "\ue338",
    210: "\ue330", 211: "\ue330", 212: "\ue330", 221: "\ue330",
    230: "\ue338", 231: "\ue338", 232: "\ue338",
    300: "\ue336", 301: "\ue336", 302: "\ue333",
    310: "\ue333", 311: "\ue333", 312: "\ue333",
    313: "\ue333", 314: "\ue333", 321: "\ue336",
    500: "\ue336", 501: "\ue333", 502: "\ue333", 503: "\ue333", 504: "\ue333",
    511: "\ue331", 520: "\ue334", 521: "\ue334", 522: "\ue334", 531: "\ue337",
    600: "\ue335", 601: "\ue335", 602: "\ue335",
    611: "\ue331", 612: "\ue331", 613: "\ue331",
    615: "\ue331", 616: "\ue331", 620: "\ue331", 621: "\ue335", 622: "\ue335",
    701: "\ue313", 711: "\ue35c", 721: "\ue3ae", 731: "\ue35d",
    741: "\ue346", 751: "\ue35d", 761: "\ue35d", 762: "\ue35d",
    771: "\ue32c", 781: "\ue351",
    800: "\ue32b",
    801: "\ue32c", 802: "\ue32c", 803: "\ue32c", 804: "\ue37e",
}

FALLBACK = {
    "temp": "--",
    "high": "--",
    "low": "--",
    "feels_like": "--",
    "condition": "Erro",
    "icon": "\ue374",
    "humidity": 0,
    "pop": 0,
    "hourly": []
}


def get_icon(code, icon_code=""):
    if icon_code.endswith("n"):
        return ICONS_NIGHT.get(code, "\ue313")
    return ICONS_DAY.get(code, "\ue30d")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main():
    key_file = os.path.join(CONFIG_DIR, "owm-key")
    loc_file = os.path.join(CONFIG_DIR, "location")

    if not os.path.exists(key_file) or not os.path.exists(loc_file):
        out = dict(FALLBACK)
        out["condition"] = "Configurar API"
        print(json.dumps(out))
        return

    api_key = open(key_file).read().strip()
    lat, lon = [v.strip() for v in open(loc_file).read().strip().split(",")]

    # Current weather
    current_url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br"
    )
    try:
        current = fetch_json(current_url)
    except urllib.error.HTTPError as e:
        msg = "API key inválida" if e.code == 401 else f"Erro {e.code}"
        out = dict(FALLBACK)
        out["condition"] = msg
        print(json.dumps(out, ensure_ascii=False))
        return

    temp = round(current["main"]["temp"])
    feels_like = round(current["main"]["feels_like"])
    humidity = current["main"]["humidity"]
    code = current["weather"][0]["id"]
    owm_icon = current["weather"][0].get("icon", "")
    condition = current["weather"][0].get("description", current["weather"][0]["main"])
    icon = get_icon(code, owm_icon)

    # Forecast (3-hour intervals) — 8 slots = 24h
    forecast_url = (
        f"https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br&cnt=8"
    )
    forecast_data = fetch_json(forecast_url)

    today = datetime.date.today()
    high = -999
    low = 999
    max_pop = 0
    hourly = []

    for entry in forecast_data["list"]:
        dt = datetime.datetime.fromtimestamp(entry["dt"])
        entry_code = entry["weather"][0]["id"]
        entry_owm_icon = entry["weather"][0].get("icon", "")
        pop = round(entry.get("pop", 0) * 100)

        # Hourly: next 4 slots (12h of 3h intervals)
        if len(hourly) < 4:
            hourly.append({
                "time": f"{dt.hour}h",
                "temp": round(entry["main"]["temp"]),
                "icon": get_icon(entry_code, entry_owm_icon),
                "desc": entry["weather"][0].get("description", ""),
                "pop": pop
            })

        # Today's high/low and max rain probability
        if dt.date() == today:
            high = max(high, entry["main"]["temp_max"])
            low = min(low, entry["main"]["temp_min"])
            max_pop = max(max_pop, pop)

    high = round(high) if high > -999 else temp
    low = round(low) if low < 999 else temp

    print(json.dumps({
        "temp": temp,
        "high": high,
        "low": low,
        "feels_like": feels_like,
        "condition": condition,
        "icon": icon,
        "humidity": humidity,
        "pop": max_pop,
        "hourly": hourly
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps(FALLBACK))
