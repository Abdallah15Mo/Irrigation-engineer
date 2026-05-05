from weather.weather_api import get_weather, get_forecast
from models.et_model import calculate_et0, calculate_etc, water_need
from models.forecast import extract_forecast_features
lat, lon = 30, 31

weather = get_weather(lat, lon)
forecast = get_forecast(lat, lon)

et0 = calculate_et0(weather["temp"], weather["humidity"], weather["wind"])
etc = calculate_etc(et0)

f_et, f_rain = extract_forecast_features(forecast)

water = water_need(etc, weather.get("rain", 0))

print("ET0:", et0)
print("ETc:", etc)
print("Water Need:", water)

from rl.multi_env import MultiZoneEnv
import random

env = MultiZoneEnv(n_zones=3)

states = env.reset()

done = False

while not done:

    actions = [random.randint(0,1) for _ in range(3)]

    states, rewards, done = env.step(
        actions,
        forecast_et=2.5,
        forecast_rain=0.3
    )

    print("Rewards:", rewards)