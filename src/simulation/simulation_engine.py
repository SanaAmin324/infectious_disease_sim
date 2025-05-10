import numpy as np
import random
import json
import os
import pygame
from collections import defaultdict

# Default values
DEFAULT_INFECTION_RADIUS = 10
DEFAULT_INFECTION_PROB = 0.2
DEFAULT_RECOVERY_TIME = 600
DEFAULT_SPEED = 2.0
GRID_SIZE = 20

# Current simulation parameters
INFECTION_RADIUS = DEFAULT_INFECTION_RADIUS
INFECTION_PROB = DEFAULT_INFECTION_PROB
RECOVERY_TIME = DEFAULT_RECOVERY_TIME
SPEED = DEFAULT_SPEED

def update_simulation_parameters(infection_radius=None, infection_prob=None, recovery_time=None, speed=None):
    global INFECTION_RADIUS, INFECTION_PROB, RECOVERY_TIME, SPEED
    if infection_radius is not None:
        INFECTION_RADIUS = infection_radius
    if infection_prob is not None:
        INFECTION_PROB = infection_prob
    if recovery_time is not None:
        RECOVERY_TIME = recovery_time
    if speed is not None:
        SPEED = speed

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
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_path = os.path.join(root_dir, filepath)

    with open(full_path, "r") as f:
        data = json.load(f)

    # Generate more nodes if needed, but limit to 100 for optimal performance
    current_nodes = len(data["nodes"])
    target_nodes = 100
    if current_nodes < target_nodes:
        additional_nodes = target_nodes - current_nodes
        for i in range(additional_nodes):
            new_node = {
                "id": current_nodes + i,
                "status": "healthy",
                "position": [
                    random.uniform(0, 800),
                    random.uniform(0, 800)
                ],
                "velocity": [
                    random.uniform(-1, 1),
                    random.uniform(-1, 1)
                ],
                "infection_timer": 0,
                "infection_type": None
            }
            data["nodes"].append(new_node)
    elif current_nodes > target_nodes:
        data["nodes"] = random.sample(data["nodes"], target_nodes)

    # Ensure all nodes have required fields and normalized velocities
    for node in data["nodes"]:
        if "velocity" not in node:
            node["velocity"] = [random.uniform(-1, 1), random.uniform(-1, 1)]
        if "status" not in node:
            node["status"] = "healthy"
        if "infection_timer" not in node:
            node["infection_timer"] = 0
        if "infection_type" not in node:
            node["infection_type"] = None
            
        # Normalize velocity
        vel = np.array(node["velocity"])
        if np.linalg.norm(vel) > 0:
            node["velocity"] = (vel / np.linalg.norm(vel)).tolist()

    return data["nodes"], data["edges"]


def get_grid_key(pos, grid_size):
    return (int(pos[0] // grid_size), int(pos[1] // grid_size))

def reset_nodes(nodes, count=2):
    for node in nodes:
        node['status'] = 'healthy'
        node['infection_timer'] = 0
        node['infection_type'] = None
        # Ensure velocity is normalized
        vel = np.array(node['velocity'])
        if np.linalg.norm(vel) > 0:
            node['velocity'] = (vel / np.linalg.norm(vel)).tolist()
    
    # Infect initial nodes
    infected = random.sample(nodes, count)
    for node in infected:
        node['status'] = 'infected'
        node['infection_timer'] = 0
        node['infection_type'] = 'symptomatic'
    return infected

def process_infections(nodes):
    # Use spatial hashing for better performance
    grid = defaultdict(list)
    infected_nodes = []
    
    # First pass: collect infected nodes and build grid
    for i, node in enumerate(nodes):
        if node['status'] == 'infected':
            infected_nodes.append(i)
            key = get_grid_key(node['position'], GRID_SIZE)
            grid[key].append(i)
    
    # Second pass: process infections only for infected nodes
    for i in infected_nodes:
        n1 = nodes[i]
        p1 = np.array(n1['position'])
        key = get_grid_key(p1, GRID_SIZE)
        
        # Check only adjacent cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                neighbor_key = (key[0] + dx, key[1] + dy)
                for j in grid.get(neighbor_key, []):
                    if i == j:
                        continue
                    n2 = nodes[j]
                    if n2['status'] == 'healthy':
                        p2 = np.array(n2['position'])
                        distance = np.linalg.norm(p1 - p2)
                        
                        if distance < INFECTION_RADIUS:
                            # Calculate effective infection probability
                            distance_factor = 1 - (distance / INFECTION_RADIUS)
                            effective_prob = INFECTION_PROB * distance_factor
                            
                            # Apply mask effectiveness if scenario has it
                            if INFECTION_RADIUS > 10:  # Scenarios with masks
                                if random.random() < 0.7:  # 70% chance of wearing mask
                                    effective_prob *= (1 - 0.9)  # 90% mask effectiveness
                            
                            # Apply social distancing effect
                            if INFECTION_RADIUS < 10:  # Strong social distancing scenarios
                                effective_prob *= 0.2
                            elif INFECTION_RADIUS < 15:  # Moderate social distancing
                                effective_prob *= 0.5
                            
                            if random.random() < effective_prob:
                                n2['status'] = 'infected'
                                n2['infection_timer'] = 0
                                n2['infection_type'] = 'symptomatic'

def update_recovery(nodes):
    for node in nodes:
        if node['status'] == 'infected':
            node['infection_timer'] += 1
            if node['infection_timer'] > RECOVERY_TIME:
                # Different recovery rates based on scenario
                if RECOVERY_TIME < 500:  # Vaccination scenario
                    recovery_chance = 0.95  # 95% recovery rate
                elif RECOVERY_TIME > 1000:  # No measures scenario
                    recovery_chance = 0.3  # 30% recovery rate, 70% death rate
                elif INFECTION_RADIUS < 10:  # Social distancing scenario
                    recovery_chance = 0.6  # 60% recovery rate
                elif INFECTION_RADIUS < 15:  # Mask wearing scenario
                    recovery_chance = 0.7  # 70% recovery rate
                else:  # Lockdown scenario
                    recovery_chance = 0.8  # 80% recovery rate
                
                if random.random() < recovery_chance:
                    node['status'] = 'recovered'
                else:
                    node['status'] = 'dead'

def update_positions(nodes, area):
    # Pre-calculate area boundaries
    min_x, min_y = 0, 0
    max_x, max_y = area[2], area[3]
    
    # Pre-calculate social distancing parameters
    sd_radius = INFECTION_RADIUS * 1.5
    sd_factor = 0.8
    
    # Adjust social distancing based on scenario
    if INFECTION_RADIUS < 10:  # Strong social distancing scenarios
        sd_radius = INFECTION_RADIUS * 2
        sd_factor = 0.5
    elif INFECTION_RADIUS < 15:  # Moderate social distancing
        sd_radius = INFECTION_RADIUS * 1.5
        sd_factor = 0.7
    
    for node in nodes:
        if node['status'] == 'dead':  # Dead nodes don't move
            continue
            
        pos = np.array(node['position'])
        vel = np.array(node['velocity'])
        
        # Apply social distancing by reducing speed when near others
        for other in nodes:
            if other != node and other['status'] != 'dead':
                other_pos = np.array(other['position'])
                distance = np.linalg.norm(pos - other_pos)
                
                if distance < sd_radius:
                    vel *= sd_factor
        
        # Normalize velocity and apply speed
        vel_norm = np.linalg.norm(vel)
        if vel_norm > 0:
            vel = vel / vel_norm * SPEED
        
        # Update position
        pos += vel
        
        # Bounce off walls (optimized)
        if pos[0] < min_x:
            pos[0] = min_x
            vel[0] = abs(vel[0])
        elif pos[0] > max_x:
            pos[0] = max_x
            vel[0] = -abs(vel[0])
            
        if pos[1] < min_y:
            pos[1] = min_y
            vel[1] = abs(vel[1])
        elif pos[1] > max_y:
            pos[1] = max_y
            vel[1] = -abs(vel[1])
            
        node['position'] = pos.tolist()
        node['velocity'] = vel.tolist()
