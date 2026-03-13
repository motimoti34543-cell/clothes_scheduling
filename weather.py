"""
weather.py — OpenWeatherMap APIで天気・気温を取得
"""
import requests
from datetime import datetime, timedelta


def get_weather_forecast(city: str, api_key: str) -> list[dict]:
    """
    OpenWeatherMap 5-day/3-hour Forecast APIで今後の天気を取得し、
    日別に集約して返す。

    Returns:
        list[dict]: 各日の天気情報
        [
            {"date": "2026-03-11", "day_name": "水", "temp": 15.2, "feels_like": 14.5,
             "temp_min": 10.0, "temp_max": 18.5,
             "weather": "Clouds", "description": "曇り", "icon": "04d"},
            ...
        ]
    """
    if not api_key:
        return _fallback_forecast()

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "ja",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return _fallback_forecast()

    # 3時間ごとのデータを日別に集約
    daily: dict[str, list] = {}
    for entry in data.get("list", []):
        dt_txt = entry["dt_txt"]  # "2026-03-11 12:00:00"
        date_str = dt_txt.split(" ")[0]
        if date_str not in daily:
            daily[date_str] = []
        daily[date_str].append(entry)

    DAY_NAMES = ["月", "火", "水", "木", "金", "土", "日"]

    result = []
    for date_str in sorted(daily.keys())[:7]:
        entries = daily[date_str]
        temps = [e["main"]["temp"] for e in entries]
        feels_likes = [e["main"]["feels_like"] for e in entries]
        temp_mins = [e["main"]["temp_min"] for e in entries]
        temp_maxs = [e["main"]["temp_max"] for e in entries]

        # 12:00に最も近いエントリから天気を取得
        midday = None
        for e in entries:
            hour = int(e["dt_txt"].split(" ")[1].split(":")[0])
            if hour == 12:
                midday = e
                break
        if midday is None:
            midday = entries[len(entries) // 2]

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        result.append({
            "date": date_str,
            "day_name": DAY_NAMES[dt.weekday()],
            "temp": round(sum(temps) / len(temps), 1),
            "feels_like": round(sum(feels_likes) / len(feels_likes), 1),
            "temp_min": round(min(temp_mins), 1),
            "temp_max": round(max(temp_maxs), 1),
            "weather": midday["weather"][0]["main"],
            "description": midday["weather"][0]["description"],
            "icon": midday["weather"][0]["icon"],
        })

    return result


def get_today_weather(city: str, api_key: str) -> dict:
    """
    OpenWeatherMap Current Weather APIで今日の天気を取得。
    """
    if not api_key:
        return _fallback_today()

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "ja",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return _fallback_today()

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "day_name": ["月", "火", "水", "木", "金", "土", "日"][datetime.now().weekday()],
        "temp": round(data["main"]["temp"], 1),
        "feels_like": round(data["main"]["feels_like"], 1),
        "temp_min": round(data["main"]["temp_min"], 1),
        "temp_max": round(data["main"]["temp_max"], 1),
        "weather": data["weather"][0]["main"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
    }


WEATHER_EMOJI = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
}


def weather_emoji(weather_main: str) -> str:
    """天気名からemojiを返す。"""
    return WEATHER_EMOJI.get(weather_main, "🌤️")


def _fallback_today() -> dict:
    """APIキー未設定/エラー時のフォールバック（今日）"""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "day_name": ["月", "火", "水", "木", "金", "土", "日"][now.weekday()],
        "temp": 20.0,
        "feels_like": 20.0,
        "temp_min": 15.0,
        "temp_max": 25.0,
        "weather": "Clear",
        "description": "（天気データなし — デフォルト20℃）",
        "icon": "01d",
    }


def _fallback_forecast() -> list[dict]:
    """APIキー未設定/エラー時のフォールバック（7日間）"""
    DAY_NAMES = ["月", "火", "水", "木", "金", "土", "日"]
    now = datetime.now()
    result = []
    for i in range(7):
        dt = now + timedelta(days=i)
        # ゆるやかに気温を変動させる
        base_temp = 18 + (i % 3) * 2
        result.append({
            "date": dt.strftime("%Y-%m-%d"),
            "day_name": DAY_NAMES[dt.weekday()],
            "temp": float(base_temp),
            "feels_like": float(base_temp),
            "temp_min": float(base_temp - 5),
            "temp_max": float(base_temp + 5),
            "weather": "Clear",
            "description": "（天気データなし — デフォルト）",
            "icon": "01d",
        })
    return result
