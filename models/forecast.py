def extract_forecast_features(forecast):
    et0_list = []
    rain_list = []

    for f in forecast:

        # 🔥 حماية كاملة ضد أي missing keys
        temp = f.get("temp") or 0
        wind = f.get("wind") or 0
        humidity = f.get("humidity") or 0
        radiation = f.get("radiation") or 0

        # 🔥 حساب ET0 آمن
        et0 = (
            0.4 * temp +
            0.25 * wind +
            0.01 * (100 - humidity) * temp +
            0.001 * radiation
        )

        et0_list.append(max(0, et0))
        rain_list.append(f.get("rain") or 0)

    return et0_list, rain_list