"""
Catch-44 Network Theory Module
------------------------------
Models karma as consequence propagation through networks.

Key truths:
- Effects propagate via topology, not intention
- Hubs amplify everything
- Consequences return indirectly and delayed
- Grace reduces cascade amplitude
"""

from dataclasses import dataclass
import random


@dataclass
class Node:
    name: str
    state: float            # wellbeing / stability
    grace: float = 0.0      # damping factor (0–1)


class Network:
    def __init__(self):
        self.nodes = {}
        self.edges = {}  # adjacency: name -> list[(neighbor, weight)]

    def add_node(self, node: Node):
        self.nodes[node.name] = node
        self.edges[node.name] = []

    def connect(self, a, b, weight=1.0):
        self.edges[a].append((b, weight))
        self.edges[b].append((a, weight))

    def apply_action(self, source, impact):
        """
        Apply an action at a node.
        Positive or negative impact.
        """
        if source not in self.nodes:
            return
        self.nodes[source].state += impact

        # propagate to neighbors
        self._propagate(source, impact)

    def _propagate(self, source, impact):
        visited = set()
        queue = [(source, impact)]

        while queue:
            current, value = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for neighbor, weight in self.edges[current]:
                node = self.nodes[neighbor]

                # attenuation by edge weight and grace
                propagated = value * weight * (1 - node.grace)

                # threshold: tiny effects die out
                if abs(propagated) < 0.05:
                    continue

                node.state += propagated
                queue.append((neighbor, propagated))

    def stats(self):
        return {
            name: round(node.state, 2)
            for name, node in self.nodes.items()
        }


def run_network_simulation():
    net = Network()

    # Create nodes
    net.add_node(Node("Hub", state=10, grace=0.1))
    net.add_node(Node("A", state=10, grace=0.3))
    net.add_node(Node("B", state=10, grace=0.2))
    net.add_node(Node("C", state=10, grace=0.0))
    net.add_node(Node("D", state=10, grace=0.4))

    # Connect network (hub-and-spoke + lateral ties)
    net.connect("Hub", "A", weight=0.8)
    net.connect("Hub", "B", weight=0.9)
    net.connect("Hub", "C", weight=0.7)
    net.connect("B", "D", weight=0.6)
    net.connect("A", "C", weight=0.5)

    print("Initial State:")
    print(net.stats())

    # Ego-driven harm at the hub
    net.apply_action("Hub", impact=-5)

    print("\nAfter Harm at Hub:")
    print(net.stats())

    # Graceful response downstream
    net.apply_action("D", impact=3)

    print("\nAfter Graceful Action at Periphery:")
    print(net.stats())


if __name__ == "__main__":
    run_network_simulation()
