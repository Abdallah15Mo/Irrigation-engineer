# ================= ET0 =================
def calculate_et0(temp, humidity, wind, radiation):
    et0 = (
        0.35 * temp +
        0.3 * wind +
        0.02 * (100 - humidity) +
        0.0012 * radiation
    )
    return max(0, et0)


# ================= ETC =================
def calculate_etc(et0, kc=0.8):
    return et0 * kc


# ================= BASIC WATER =================
def water_need(etc, rainfall):
    return max(0, etc - rainfall)


def irrigation_volume(etc, area):
    return etc * area


# ================= 🔥 SMART IRRIGATION =================
def smart_irrigation_volume(etc, area, moisture, rain_forecast):
    """
    etc: evapotranspiration
    area: m²
    moisture: soil moisture (%)
    rain_forecast: expected rain (mm)
    """

    # 🌱 soil moisture factor
    if moisture < 30:
        factor = 1.3
    elif moisture < 50:
        factor = 1.0
    else:
        factor = 0.6

    # 🌧 rain effect
    rain_effect = max(0, rain_forecast * 0.7)

    # 💧 final water depth
    water_mm = max(0, etc - rain_effect) * factor

    # 🚜 liters
    water_liters = water_mm * area

    return water_mm, water_liters