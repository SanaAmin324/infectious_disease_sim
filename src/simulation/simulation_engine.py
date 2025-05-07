import numpy as np
import random
import json
import os
import pygame
INFECTION_RADIUS = 10
INFECTION_PROB = 0.2
RECOVERY_TIME = 600
SPEED = 1.5
GRID_SIZE = 20

class Simulation:
    def __init__(self, nodes, edges, policy=None):
        self.nodes = nodes
        self.edges = edges
        self.policy = policy
        self.day = 0

        self.initialize_nodes()
        self.apply_policy()

    def initialize_nodes(self):
        for node in self.nodes:
            node["state"] = "susceptible"

        # Infect a few randomly
        import random
        for node in random.sample(self.nodes, k=5):
            node["state"] = "infected"

    def apply_policy(self):
        if self.policy == "lockdown":
            for edge in self.edges:
                edge["weight"] *= 0.2  # Reduce contact rate
        elif self.policy == "vaccination":
            for node in self.nodes[:100]:  # Vaccinate first 100
                node["state"] = "recovered"

    def update(self):
        # Fake update logic: just increment day
        self.day += 1

    def draw(self, surface):
        surface.fill((255, 255, 255))
        font = pygame.font.SysFont(None, 24)
        title = f"{'Policy' if self.policy else 'Standard'} Day {self.day}"
        text = font.render(title, True, (0, 0, 0))
        surface.blit(text, (20, 20))


def load_network(filepath):
    # Get the path to the *project root* (i.e., one level up from /src)
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_path = os.path.join(root_dir, filepath)

    print(f"[DEBUG] Loading network from: {full_path}")  # optional debug line

    with open(full_path, "r") as f:
        data = json.load(f)

    return data["nodes"], data["edges"]


def get_grid_key(pos, grid_size):
    return (int(pos[0] // grid_size), int(pos[1] // grid_size))

def reset_nodes(nodes, count=3):
    for node in nodes:
        node['status'] = 'healthy'
        node['infection_timer'] = 0
        node['infection_type'] = None
    infected = random.sample(nodes, count)
    for node in infected:
        node['status'] = 'infected'
        node['infection_timer'] = 0
        node['infection_type'] = 'symptomatic'
    return infected

def update_positions(nodes, area):
    for node in nodes:
        pos = np.array(node['position'])
        vel = np.array(node['velocity'])
        pos += vel * SPEED
        if pos[0] < 0 or pos[0] > area[2]:
            vel[0] *= -1
        if pos[1] < 0 or pos[1] > area[3]:
            vel[1] *= -1
        node['position'] = pos
        node['velocity'] = vel

def process_infections(nodes):
    grid = {}
    for i, node in enumerate(nodes):
        key = get_grid_key(node['position'], GRID_SIZE)
        grid.setdefault(key, []).append(i)

    for key, indices in grid.items():
        x, y = key
        neighbors = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]
        for i in indices:
            n1 = nodes[i]
            if n1['status'] != 'infected':
                continue
            p1 = np.array(n1['position'])
            for nk in neighbors:
                for j in grid.get(nk, []):
                    if i == j:
                        continue
                    n2 = nodes[j]
                    if n2['status'] == 'healthy':
                        p2 = np.array(n2['position'])
                        if np.linalg.norm(p1 - p2) < INFECTION_RADIUS:
                            if random.random() < INFECTION_PROB:
                                n2['status'] = 'infected'
                                n2['infection_timer'] = 0
                                n2['infection_type'] = 'symptomatic'

def update_recovery(nodes):
    for node in nodes:
        if node['status'] == 'infected':
            node['infection_timer'] += 1
            if node['infection_timer'] > RECOVERY_TIME:
                node['status'] = 'recovered' if random.random() < 0.7 else 'dead'
