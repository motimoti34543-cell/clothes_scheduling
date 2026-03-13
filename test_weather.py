import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from weather import get_today_weather, get_weather_forecast

try:
    tw = get_today_weather("Tokyo", "")
    print(tw)
    print("feels_like in tw:", "feels_like" in tw)
except Exception as e:
    print(e)
