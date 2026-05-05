def simulate_future(moisture, forecast):

    results = []

    for i, f in enumerate(forecast[:7]):  # 7 days

        et = (
            0.4 * f["temp"] +
            0.15 * f["wind"] +
            0.02 * (100 - f["humidity"]) +
            0.001 * f["radiation"]
        ) * 0.8

        moisture -= et * 0.5
        moisture += f["rain"] * 0.3

        moisture = max(0, min(100, moisture))

        results.append({
            "day": i + 1,
            "moisture": moisture,
            "et": et,
            "rain": f["rain"]
        })

    return results


def irrigation_schedule(future, area):

    schedule = []

    for day in future:

        if day["moisture"] < 40:

            water_mm = 10  # كمية ري تقديرية

            water_liters = water_mm * area

            schedule.append({
                "day": day["day"],
                "action": "Irrigate",
                "water_liters": water_liters
            })

        else:
            schedule.append({
                "day": day["day"],
                "action": "No Irrigation",
                "water_liters": 0
            })

    return schedule