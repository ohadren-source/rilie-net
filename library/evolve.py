"""
Catch-44 Evolutionary Biology Module
-----------------------------------
Models evolutionary dynamics under Catch-44 constraints.

Key truths:
- Evolution selects for persistence, not goodness
- Harmful strategies can be locally adaptive
- Cooperation requires protection
- Understanding does not guarantee survival
"""

import random
from dataclasses import dataclass


@dataclass
class Agent:
    strategy: str  # "cooperate", "exploit"
    energy: float
    alive: bool = True


class Population:
    def __init__(self, size, coop_ratio=0.7):
        self.agents = []
        for _ in range(size):
            strategy = "cooperate" if random.random() < coop_ratio else "exploit"
            self.agents.append(Agent(strategy=strategy, energy=10))

    def interact(self):
        """
        Pairwise interactions.
        Exploiters gain short-term energy by harming cooperators.
        """
        random.shuffle(self.agents)

        for i in range(0, len(self.agents) - 1, 2):
            a, b = self.agents[i], self.agents[i + 1]

            if not a.alive or not b.alive:
                continue

            if a.strategy == "cooperate" and b.strategy == "cooperate":
                a.energy += 2
                b.energy += 2

            elif a.strategy == "exploit" and b.strategy == "cooperate":
                a.energy += 4
                b.energy -= 3

            elif a.strategy == "cooperate" and b.strategy == "exploit":
                b.energy += 4
                a.energy -= 3

            else:  # exploit / exploit
                a.energy -= 1
                b.energy -= 1

    def apply_entropy(self):
        """
        Living costs energy for all.
        """
        for agent in self.agents:
            if agent.alive:
                agent.energy -= 1
                if agent.energy <= 0:
                    agent.alive = False

    def reproduce(self):
        """
        Survivors reproduce proportional to energy.
        Offspring inherit strategy with mutation chance.
        """
        new_agents = []

        for agent in self.agents:
            if agent.alive and agent.energy >= 8:
                offspring_strategy = agent.strategy
                if random.random() < 0.05:
                    offspring_strategy = "cooperate" if agent.strategy == "exploit" else "exploit"
                new_agents.append(Agent(strategy=offspring_strategy, energy=5))

        self.agents.extend(new_agents)

    def stats(self):
        alive = [a for a in self.agents if a.alive]
        if not alive:
            return {"population": 0}

        return {
            "population": len(alive),
            "cooperate": sum(1 for a in alive if a.strategy == "cooperate"),
            "exploit": sum(1 for a in alive if a.strategy == "exploit"),
            "avg_energy": round(sum(a.energy for a in alive) / len(alive), 2),
        }


def run_simulation(generations=50):
    pop = Population(size=100, coop_ratio=0.8)

    print("Initial:", pop.stats())

    for gen in range(generations):
        pop.interact()
        pop.apply_entropy()
        pop.reproduce()

        stats = pop.stats()
        if stats["population"] == 0:
            print(f"Extinction at generation {gen}")
            break

        if gen % 5 == 0:
            print(f"Gen {gen}:", stats)

    return pop


if __name__ == "__main__":
    run_simulation()
