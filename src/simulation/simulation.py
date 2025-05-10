import pygame
import json
import numpy as np
import os
import random
import math

# Configs
WIDTH, HEIGHT = 800, 800
NODE_RADIUS = 5
SPEED = 1.5
FPS = 60
INFECTION_RADIUS = 10
INFECTION_PROB = 0.2
RECOVERY_TIME = 600  # ~10 seconds at 60 FPS

# Load network
def load_network(filepath):
    with open(filepath) as f:
        data = json.load(f)
    return data['nodes'], data['edges']

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disease Spread Simulation")
clock = pygame.time.Clock()

# Load data
nodes, edges = load_network("data/graphs/network.json")
# Infect 1 random node at start
initial_infected_count = 3
infected_nodes = random.sample(nodes, initial_infected_count)
for node in infected_nodes:
    node['status'] = 'infected'
    node['infection_timer'] = 0
    node['infection_type'] = 'symptomatic'

# Game loop
running = True
while running:
    screen.fill((30, 30, 30))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update positions and move nodes
    for node in nodes:
        pos = np.array(node['position'])
        vel = np.array(node['velocity'])

        # Move
        pos += vel * SPEED

        # Boundary bounce
        if pos[0] < 0 or pos[0] > WIDTH:
            vel[0] *= -1
        if pos[1] < 0 or pos[1] > HEIGHT:
            vel[1] *= -1

        node['position'] = pos
        node['velocity'] = vel

    # Infection spread logic
    for i, node1 in enumerate(nodes):
        if node1['status'] != 'infected':
            continue
        pos1 = np.array(node1['position'])

        for j, node2 in enumerate(nodes):
            if i == j or node2['status'] != 'healthy':
                continue
            pos2 = np.array(node2['position'])
            distance = np.linalg.norm(pos1 - pos2)
            if distance < INFECTION_RADIUS:
                if random.random() < INFECTION_PROB:
                    node2['status'] = 'infected'
                    node2['infection_timer'] = 0
                    node2['infection_type'] = 'symptomatic'

    # Update infected node timers
    for node in nodes:
        if node['status'] == 'infected':
            node['infection_timer'] += 1
            if node['infection_timer'] > RECOVERY_TIME:
                if random.random() < 0.7:
                    node['status'] = 'recovered'
                else:
                    node['status'] = 'dead'

    # Draw nodes
    for node in nodes:
        pos = np.array(node['position'])
        status = node['status']
        color = {
            'healthy': (0, 200, 0),
            'infected': (255, 0, 0),
            'recovered': (0, 100, 255),
            'dead': (100, 100, 100)
        }.get(status, (255, 255, 255))

        pygame.draw.circle(screen, color, pos.astype(int), NODE_RADIUS)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
