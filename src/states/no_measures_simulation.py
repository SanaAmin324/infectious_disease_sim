import pygame
import numpy as np
import random
from simulation.simulation_engine import load_network, update_positions, process_infections, update_recovery, reset_nodes

class NoMeasuresSimulation:
    def __init__(self, screen, scenario="No Measures"):
        self.screen = screen
        self.current_scenario = scenario
        self.nodes, self.edges = load_network("data/graphs/network.json")
        
        # No measures specific parameters (more severe than standard)
        self.INFECTION_RADIUS = 20  # Larger infection radius
        self.INFECTION_PROB = 0.35  # Higher infection probability
        self.RECOVERY_TIME = 600    # Shorter recovery time
        self.SPEED = 2.0           # Faster movement
        self.BASIC_PRECAUTIONS = False  # No precautions
        self.PRECAUTION_FACTOR = 0.0    # No reduction in infection probability
        
        # Initialize simulation
        self.infected_nodes = reset_nodes(self.nodes)
        self.paused = False
        self.frame_count = 0
        self.day_counter = 0
        self.frames_per_day = 30
        self.sim_speed = 1
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        
        # Statistics tracking
        self.healthy_data = []
        self.infected_data = []
        self.recovered_data = []
        self.dead_data = []
        
        # Colors
        self.BG_COLOR = (30, 30, 30)
        self.SIMULATION_COLOR = (40, 40, 40)
        
        # Setup simulation area
        self.update_simulation_dimensions()
        
    def update_simulation_dimensions(self):
        screen_width, screen_height = self.screen.get_size()
        self.simulation_width = int(screen_width * 0.8)
        self.SIMULATION_AREA = (0, 0, self.simulation_width, screen_height)
        
        # Reposition nodes to fill simulation area
        for node in self.nodes:
            if node['status'] != 'dead':
                node['position'] = [
                    random.uniform(0, self.simulation_width),
                    random.uniform(0, screen_height)
                ]
    
    def process_infections(self):
        for i, node1 in enumerate(self.nodes):
            if node1['status'] == 'infected':
                for j, node2 in enumerate(self.nodes):
                    if i != j and node2['status'] == 'healthy':
                        pos1 = np.array(node1['position'])
                        pos2 = np.array(node2['position'])
                        distance = np.linalg.norm(pos1 - pos2)
                        
                        if distance < self.INFECTION_RADIUS:
                            # Calculate effective infection probability
                            effective_prob = self.INFECTION_PROB
                            
                            # Apply basic precautions if enabled
                            if self.BASIC_PRECAUTIONS:
                                effective_prob *= (1 - self.PRECAUTION_FACTOR)
                            
                            if random.random() < effective_prob:
                                node2['status'] = 'infected'
                                node2['infection_timer'] = 0
    
    def update_recovery(self):
        for node in self.nodes:
            if node['status'] == 'infected':
                node['infection_timer'] += 1
                if node['infection_timer'] > self.RECOVERY_TIME:
                    # No Measures: 50% recovery rate, 50% death rate
                    if random.random() < 0.5:
                        node['status'] = 'recovered'
                    else:
                        node['status'] = 'dead'
    
    def update(self):
        if not self.paused:
            self.frame_count += self.sim_speed
            self.day_counter = self.frame_count // self.frames_per_day
            
            # Update multiple times based on speed
            for _ in range(self.sim_speed):
                update_positions(self.nodes, self.SIMULATION_AREA)
                self.process_infections()
                self.update_recovery()
            
            # Update statistics
            self.healthy_data.append(sum(1 for n in self.nodes if n['status'] == 'healthy'))
            self.infected_data.append(sum(1 for n in self.nodes if n['status'] == 'infected'))
            self.recovered_data.append(sum(1 for n in self.nodes if n['status'] == 'recovered'))
            self.dead_data.append(sum(1 for n in self.nodes if n['status'] == 'dead'))
    
    def draw(self):
        # Draw simulation area
        pygame.draw.rect(self.screen, self.SIMULATION_COLOR, self.SIMULATION_AREA)
        
        # Draw nodes
        for node in self.nodes:
            pos = node['position']
            color = {
                'healthy': (0, 200, 0),    # Green
                'infected': (255, 0, 0),   # Red
                'recovered': (0, 100, 255), # Blue
                'dead': (100, 100, 100)    # Gray
            }.get(node['status'], (255, 255, 255))
            
            # Draw node
            pygame.draw.circle(self.screen, color, [int(p) for p in pos], 3)
            
            # Draw warning indicator for no measures scenario
            if self.current_scenario == "No Measures" and node['status'] == 'healthy':
                pygame.draw.circle(self.screen, (255, 165, 0), [int(p) for p in pos], 5, 1)  # Orange warning ring
            # Draw precaution indicator for standard scenario
            elif self.current_scenario == "Standard" and node['status'] == 'healthy':
                pygame.draw.circle(self.screen, (0, 255, 255), [int(p) for p in pos], 5, 1)  # Cyan precaution ring
        
        # Draw statistics
        self.draw_statistics()
    
    def draw_statistics(self):
        stats_y = 10
        font = pygame.font.SysFont(None, 24)
        
        # Draw day counter first
        day_text = font.render(f"Day: {self.day_counter}", True, (255, 255, 255))
        self.screen.blit(day_text, (self.simulation_width + 10, stats_y))
        stats_y += 30
        
        # Draw divider line
        pygame.draw.line(self.screen, (60, 60, 70), 
                        (self.simulation_width + 10, stats_y),
                        (self.simulation_width + 190, stats_y), 2)
        stats_y += 20
        
        stats = {
            'Healthy': (self.healthy_data[-1] if self.healthy_data else 0, (0, 200, 0)),
            'Infected': (self.infected_data[-1] if self.infected_data else 0, (255, 0, 0)),
            'Recovered': (self.recovered_data[-1] if self.recovered_data else 0, (0, 100, 255)),
            'Dead': (self.dead_data[-1] if self.dead_data else 0, (100, 100, 100))
        }
        
        for label, (value, color) in stats.items():
            text = font.render(f"{label}: {value}", True, color)
            self.screen.blit(text, (self.simulation_width + 10, stats_y))
            stats_y += 30 