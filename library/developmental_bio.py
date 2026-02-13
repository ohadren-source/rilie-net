"""
Catch-44 Developmental Biology Module
------------------------------------
Models biological development with critical periods.

Key truths:
- Timing matters more than intensity
- Some structures can only form once
- Late intervention is costlier and incomplete
- Early harm is amplified across lifespan
"""

from dataclasses import dataclass


@dataclass
class DevelopingSystem:
    name: str
    age: int
    critical_window_end: int
    development_level: float     # 0–100
    potential: float             # max achievable
    damaged: bool = False


class DevelopmentalModel:
    def __init__(self):
        self.time = 0
        self.systems = []

    def add_system(self, system: DevelopingSystem):
        self.systems.append(system)

    def nurture(self, effort):
        """
        Positive input (nutrition, care, learning).
        """
        for s in self.systems:
            if s.age <= s.critical_window_end:
                gain = effort * 1.5   # high leverage early
            else:
                gain = effort * 0.4   # diminishing returns

            s.development_level = min(
                s.potential,
                s.development_level + gain
            )

    def apply_harm(self, magnitude):
        """
        Harm during development permanently lowers potential.
        """
        for s in self.systems:
            if s.age <= s.critical_window_end:
                # irreversible developmental damage
                s.potential -= magnitude * 0.8
                s.development_level -= magnitude * 0.5
                s.damaged = True
            else:
                # harm later is partially recoverable
                s.development_level -= magnitude * 0.3

            if s.development_level < 0:
                s.development_level = 0
            if s.potential < 0:
                s.potential = 0

    def age_forward(self):
        """
        Advance developmental time.
        """
        self.time += 1
        for s in self.systems:
            s.age += 1

    def status(self):
        return {
            "time": self.time,
            "systems": {
                s.name: {
                    "age": s.age,
                    "development": round(s.development_level, 2),
                    "potential": round(s.potential, 2),
                    "critical_window_open": s.age <= s.critical_window_end,
                    "damaged": s.damaged
                } for s in self.systems
            }
        }


def run_development_simulation():
    model = DevelopmentalModel()

    model.add_system(DevelopingSystem(
        name="Human Child",
        age=0,
        critical_window_end=10,
        development_level=5,
        potential=100
    ))

    print("Initial State:")
    print(model.status())

    # Early years
    for _ in range(5):
        model.nurture(effort=5)
        model.age_forward()

    # Early harm
    model.apply_harm(magnitude=10)

    print("\nAfter Early Harm:")
    print(model.status())

    # Later heavy intervention
    for _ in range(15):
        model.nurture(effort=15)
        model.age_forward()

    print("\nAfter Late Intervention:")
    print(model.status())


if __name__ == "__main__":
    run_development_simulation()
