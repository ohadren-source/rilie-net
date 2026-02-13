"""
Catch-44 Deep Time / Geology Module
----------------------------------
Models slow, irreversible processes with delayed feedback.

Key truths:
- Cause and effect are separated by time
- Damage can be invisible for generations
- Thresholds trigger abrupt phase shifts
- Responsibility exists without witnesses
"""

from dataclasses import dataclass


@dataclass
class GeologicalSystem:
    name: str
    stability: float        # perceived stability (0–100)
    accumulated_stress: float
    threshold: float        # collapse point
    recovery_rate: float    # very slow
    collapsed: bool = False


class DeepTimeModel:
    def __init__(self):
        self.time = 0
        self.systems = []

    def add_system(self, system: GeologicalSystem):
        self.systems.append(system)

    def apply_action(self, stress, intent="benign"):
        """
        Human-scale action with geological-scale consequences.
        """
        for s in self.systems:
            if not s.collapsed:
                s.accumulated_stress += stress
        return {
            "intent": intent,
            "stress_added": stress,
            "visible_effect": "none"
        }

    def tick(self):
        """
        One deep-time step (centuries, millennia).
        """
        self.time += 1

        for s in self.systems:
            if s.collapsed:
                # Recovery is extremely slow
                s.accumulated_stress = max(
                    0,
                    s.accumulated_stress - s.recovery_rate
                )
                if s.accumulated_stress < s.threshold * 0.6:
                    s.collapsed = False
            else:
                # Stability illusion
                s.stability = max(
                    0,
                    100 - (s.accumulated_stress / s.threshold) * 100
                )

                if s.accumulated_stress >= s.threshold:
                    s.collapsed = True

    def status(self):
        return {
            "deep_time": self.time,
            "systems": {
                s.name: {
                    "stability": round(s.stability, 2),
                    "stress": round(s.accumulated_stress, 2),
                    "collapsed": s.collapsed
                } for s in self.systems
            }
        }


def run_deep_time_simulation():
    earth = DeepTimeModel()

    earth.add_system(GeologicalSystem(
        name="Climate System",
        stability=100,
        accumulated_stress=0,
        threshold=1000,
        recovery_rate=1
    ))

    earth.add_system(GeologicalSystem(
        name="Biosphere",
        stability=100,
        accumulated_stress=0,
        threshold=800,
        recovery_rate=0.5
    ))

    print("Initial State:")
    print(earth.status())

    # Human era: many small actions
    for _ in range(50):
        earth.apply_action(stress=10, intent="progress")
        earth.tick()

    print("\nAfter Human Era:")
    print(earth.status())

    # Long silence — consequences unfold
    for _ in range(500):
        earth.tick()

    print("\nFar Future:")
    print(earth.status())


if __name__ == "__main__":
    run_deep_time_simulation()
