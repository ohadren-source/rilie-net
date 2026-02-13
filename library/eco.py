"""
Catch-44 Ecology Module
----------------------
Models ecological systems under Catch-44 constraints.

Key truths:
- Systems collapse from local optimization
- Harm propagates across species
- Keystone actors matter disproportionately
- Carrying capacity is non-negotiable
"""

import random
from dataclasses import dataclass


@dataclass
class Species:
    name: str
    population: int
    consumption_rate: float   # resource units per individual
    reproduction_rate: float  # fractional growth
    keystone: bool = False
    alive: bool = True


class Ecosystem:
    def __init__(self, resource_pool, regen_rate):
        self.resource_pool = resource_pool
        self.regen_rate = regen_rate
        self.species = []

    def add_species(self, species: Species):
        self.species.append(species)

    def step(self):
        """
        One ecological timestep.
        """
        # Resource regeneration
        self.resource_pool += self.regen_rate

        # Total consumption
        total_consumption = 0
        for s in self.species:
            if s.alive:
                total_consumption += s.population * s.consumption_rate

        # Resource constraint
        if total_consumption > self.resource_pool:
            shortage_ratio = self.resource_pool / total_consumption
        else:
            shortage_ratio = 1.0

        # Apply effects to species
        for s in self.species:
            if not s.alive:
                continue

            # Population change
            growth = int(s.population * s.reproduction_rate * shortage_ratio)
            s.population += growth

            # Starvation
            if shortage_ratio < 0.7:
                loss = int(s.population * (1 - shortage_ratio))
                s.population -= loss

            if s.population <= 0:
                s.population = 0
                s.alive = False

        # Resource depletion
        self.resource_pool -= min(total_consumption, self.resource_pool)

        # Keystone collapse propagation
        for s in self.species:
            if s.keystone and not s.alive:
                self._keystone_collapse(s)

    def _keystone_collapse(self, keystone_species):
        """
        Loss of keystone species destabilizes others.
        """
        for s in self.species:
            if s.alive and s is not keystone_species:
                s.population = int(s.population * 0.5)

    def apply_harm(self, target_name, magnitude):
        """
        Intentional harm to one species.
        """
        for s in self.species:
            if s.name == target_name and s.alive:
                s.population -= magnitude
                if s.population <= 0:
                    s.population = 0
                    s.alive = False

    def stats(self):
        return {
            "resources": round(self.resource_pool, 2),
            "species": {
                s.name: {
                    "population": s.population,
                    "alive": s.alive,
                    "keystone": s.keystone
                } for s in self.species
            }
        }


def run_ecology_simulation(steps=30):
    eco = Ecosystem(resource_pool=1000, regen_rate=80)

    eco.add_species(Species(
        name="Plants",
        population=500,
        consumption_rate=0.5,
        reproduction_rate=0.1,
        keystone=True
    ))

    eco.add_species(Species(
        name="Herbivores",
        population=120,
        consumption_rate=2.0,
        reproduction_rate=0.08
    ))

    eco.add_species(Species(
        name="Predators",
        population=40,
        consumption_rate=3.0,
        reproduction_rate=0.05
    ))

    print("Initial State:")
    print(eco.stats())

    for step in range(steps):
        eco.step()

        if step == 10:
            # Local optimization / harm
            eco.apply_harm("Plants", magnitude=200)

        if step % 5 == 0:
            print(f"\nStep {step}")
            print(eco.stats())

    return eco


if __name__ == "__main__":
    run_ecology_simulation()
