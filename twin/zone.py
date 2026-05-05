from twin.soil_model import SoilModel
from twin.crop_model import TurfModel

class Zone:

    def __init__(self, id):

        self.id = id
        self.soil = SoilModel()
        self.crop = TurfModel()

        self.history = []

    def step(self, irrigation, weather):

        moisture = self.soil.step(irrigation, weather["et"], weather["rain"])
        health = self.crop.step(moisture)

        state = {
            "moisture": moisture,
            "health": health
        }

        self.history.append(state)

        return state