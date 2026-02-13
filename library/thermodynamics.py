"""
Catch-44 Thermodynamics Module
--------------------------------
This module models thermodynamic constraints through the Catch-44 framework.

Key ideas:
- Entropy is non-negotiable
- Order requires continuous work
- Some harm is irreversible
- Minimizing harm does NOT mean eliminating cost
- Ethics cannot violate physics

Designed to fail loudly when assumptions break.
"""

import math


class ThermodynamicSystem:
    def __init__(self, energy, entropy, order, name="System"):
        """
        energy: total usable energy
        entropy: disorder level (>= 0)
        order: structured complexity maintained by energy
        """
        self.name = name
        self.energy = energy
        self.entropy = entropy
        self.order = order

        self.validate_state()

    def validate_state(self):
        if self.energy < 0:
            raise ValueError("Energy cannot be negative.")
        if self.entropy < 0:
            raise ValueError("Entropy cannot be negative.")
        if self.order < 0:
            raise ValueError("Order cannot be negative.")
        if self.order > self.energy:
            raise ValueError(
                "Order cannot exceed available energy. "
                "Physics violated."
            )

    def maintain_order(self, effort):
        """
        Maintaining order requires energy expenditure.
        Some energy is always lost to entropy.
        """
        if effort > self.energy:
            raise RuntimeError(
                "Attempted to maintain order without sufficient energy."
            )

        entropy_generated = effort * 0.25  # irreducible loss
        useful_work = effort - entropy_generated

        self.energy -= effort
        self.order += useful_work
        self.entropy += entropy_generated

        self.validate_state()

    def apply_harm(self, magnitude):
        """
        Harm increases entropy and reduces order.
        Some harm is irreversible.
        """
        irreversible_fraction = 0.4
        reversible_fraction = 0.6

        irreversible_damage = magnitude * irreversible_fraction
        reversible_damage = magnitude * reversible_fraction

        self.order -= magnitude
        self.entropy += irreversible_damage

        if self.order < 0:
            self.order = 0  # collapse

        return {
            "irreversible": irreversible_damage,
            "reversible": reversible_damage,
        }

    def attempt_repair(self, effort):
        """
        Attempt to repair damage.
        Irreversible harm cannot be undone.
        """
        if effort > self.energy:
            raise RuntimeError(
                "Repair attempted without sufficient energy."
            )

        repair_efficiency = 0.6
        entropy_cost = effort * 0.3

        restored_order = effort * repair_efficiency

        self.energy -= effort
        self.order += restored_order
        self.entropy += entropy_cost

        self.validate_state()

    def status(self):
        return {
            "name": self.name,
            "energy": round(self.energy, 3),
            "order": round(self.order, 3),
            "entropy": round(self.entropy, 3),
        }


# Catch-44 ethical constraint check
def catch44_integrity_check(claimed_repair, actual_repair):
    """
    Claim + Deed = Integrity
    """
    if claimed_repair > actual_repair:
        raise AssertionError(
            "Integrity violation: Claim exceeded deed."
        )


def run_demo():
    """
    Demonstrates:
    - Irreversibility
    - Cost of order
    - Failure of 'perfect repair'
    """
    system = ThermodynamicSystem(
        energy=100,
        entropy=10,
        order=50,
        name="Living System"
    )

    print("Initial:", system.status())

    # Maintain order
    system.maintain_order(effort=20)
    print("After maintenance:", system.status())

    # Apply harm
    damage = system.apply_harm(magnitude=30)
    print("After harm:", system.status())
    print("Damage breakdown:", damage)

    # Attempt repair
    pre_order = system.order
    system.attempt_repair(effort=25)
    actual_repair = system.order - pre_order

    catch44_integrity_check(
        claimed_repair=25,  # false claim of full repair
        actual_repair=actual_repair
    )

    print("After repair attempt:", system.status())


if __name__ == "__main__":
    run_demo()
