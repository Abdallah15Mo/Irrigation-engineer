import random
import numpy as np


# ================= ZONE =================
class Zone:
    def __init__(self, zone_id):
        self.id = zone_id
        self.moisture = random.uniform(40, 60)

    def get_state(self, forecast_et, forecast_rain):
        return np.array([
            self.moisture / 100,
            forecast_et / 10,
            forecast_rain / 10
        ])


# ================= ENV =================
class MultiZoneEnv:

    def __init__(self, n_zones, max_steps=30):
        self.n_zones = n_zones
        self.max_steps = max_steps
        self.current_step = 0

        self.zones = [Zone(i) for i in range(n_zones)]

    def reset(self):
        self.current_step = 0

        for z in self.zones:
            z.moisture = random.uniform(40, 60)

        return self._get_states(0, 0)

    def _get_states(self, forecast_et, forecast_rain):
        return np.array([
            z.get_state(forecast_et, forecast_rain)
            for z in self.zones
        ])

    def step(self, actions, forecast_et, forecast_rain):

        self.current_step += 1

        rewards = []
        next_states = []

        for i, zone in enumerate(self.zones):

            # 💧 action = كمية المياه (0 → 20 لتر)
            water_amount = np.clip(actions[i], 0, 20)

            # 🔄 تحويل لتر → تأثير رطوبة
            irrigation_effect = water_amount * 0.5

            # 🌱 تحديث الرطوبة
            zone.moisture += irrigation_effect
            zone.moisture -= forecast_et * 0.4
            zone.moisture += forecast_rain * 0.3

            zone.moisture = max(0, min(100, zone.moisture))

            # ================= REWARD =================
            reward = 0

            # 🎯 الهدف المثالي
            if 45 <= zone.moisture <= 65:
                reward += 10
            else:
                reward -= abs(zone.moisture - 55) * 0.2

            # 🚫 تقليل استهلاك المياه
            reward -= water_amount * 0.1

            # ⚠️ stress penalty
            if zone.moisture < 30 or zone.moisture > 80:
                reward -= 8

            rewards.append(reward)

            next_states.append(
                zone.get_state(forecast_et, forecast_rain)
            )

        done = self.current_step >= self.max_steps

        return np.array(next_states), np.array(rewards), done

    def get_moisture_levels(self):
        return [z.moisture for z in self.zones]