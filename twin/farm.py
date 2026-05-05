from twin.zone import Zone

class Farm:

    def __init__(self, n_zones):

        self.zones = [Zone(i) for i in range(n_zones)]

    def step(self, actions, weather):

        states = []

        for i, zone in enumerate(self.zones):

            irrigation = 10 if actions[i] == 1 else 0

            state = zone.step(irrigation, weather)

            states.append(state)

        return states