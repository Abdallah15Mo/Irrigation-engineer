import requests
import math
from datetime import datetime

API_KEY = "b5513ecccbdb684f0494d74fe02a6143"


def get_weather(lat, lon):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if r.status_code != 200 or "main" not in data:
            print("Weather API Error:", data)
            return None

        # 🌞 تقدير الإشعاع الشمسي (correct)
        hour = datetime.now().hour
        radiation = max(0, 800 * math.sin((hour - 6) / 12 * 3.1416))

        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"],
            "description": data["weather"][0]["description"],
            "radiation": radiation
        }

    except Exception as e:
        print("Weather Exception:", e)
        return None


def get_forecast(lat, lon):
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"

        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if r.status_code != 200 or "list" not in data:
            print("Forecast API Error:", data)
            return []
        forecast = []
        for item in data["list"]:
            hour = int(item["dt_txt"].split(" ")[1].split(":")[0])
            forecast.append({
                "temp": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "wind": item["wind"]["speed"],
                "rain": item.get("rain", {}).get("3h", 0),
                "radiation": max(0, 800 * math.sin((hour - 6) / 12 * 3.1416)),
                "time": item["dt_txt"]
            })

        return forecast

    except Exception as e:
        print("Forecast Exception:", e)
        return []