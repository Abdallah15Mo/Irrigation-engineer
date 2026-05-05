class SoilModel:

    def __init__(self):
        self.moisture = 50

    def step(self, irrigation, et, rain):

        self.moisture += irrigation
        self.moisture -= et * 0.5
        self.moisture += rain * 0.3

        self.moisture = max(0, min(100, self.moisture))

        return self.moisture