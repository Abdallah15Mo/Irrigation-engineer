class TurfModel:

    def __init__(self):
        self.health = 1.0

    def step(self, moisture):

        if 40 <= moisture <= 70:
            self.health += 0.01
        else:
            self.health -= 0.02

        self.health = max(0, min(1, self.health))

        return self.health