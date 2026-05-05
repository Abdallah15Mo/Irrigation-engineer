print("DIAG START")
import importlib, traceback
modules = [
    "weather.weather_api",
    "models.et_model",
    "models.forecast",
    "twin.farm",
    "twin.zone",
    "twin.soil_model",
    "twin.crop_model",
    "rl.transformer_agent"
]
for m in modules:
    try:
        mod = importlib.import_module(m)
        print(f"imported {m}: {mod}")
    except Exception as e:
        print(f"FAILED {m}: {e}")
        traceback.print_exc()
print("DIAG END")
