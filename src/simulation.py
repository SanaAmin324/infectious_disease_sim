import pygame
import json
import numpy as np
import random
from pygame.locals import *

# Configs
WIDTH, HEIGHT = 1000, 800
SIMULATION_AREA = (0, 0, 800, 800)  # Left area for simulation
CONTROL_PANEL = (800, 0, 200, 800)   # Right area for controls
NODE_RADIUS = 2
SPEED = 1.5
FPS = 30
INFECTION_RADIUS = 10
INFECTION_PROB = 0.2
RECOVERY_TIME = 600  # ~20 seconds at 30 FPS
SIM_SPEED = 1

# Colors
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (50, 50, 60)
BUTTON_COLOR = (70, 70, 80)
BUTTON_HOVER = (90, 90, 100)
TEXT_COLOR = (255, 255, 255)

def load_network(filepath):
    with open(filepath) as f:
        data = json.load(f)
    return data['nodes'], data['edges']

def get_grid_key(pos, grid_size):
    return (int(pos[0] // grid_size), int(pos[1] // grid_size))

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        
    def draw(self, surface):
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (100, 100, 110), self.rect, 2, border_radius=5)
        
        font = pygame.font.SysFont(None, 24)
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disease Spread Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# Load data
nodes, edges = load_network("data/graphs/network.json")
initial_infected_count = 3
infected_nodes = random.sample(nodes, initial_infected_count)
for node in infected_nodes:
    node['status'] = 'infected'
    node['infection_timer'] = 0
    node['infection_type'] = 'symptomatic'

# Simulation state
paused = False
frame_count = 0
day_counter = 0
frames_per_day = FPS * 1
GRID_SIZE = 20

# Create control panel buttons
pause_button = Button(820, 100, 160, 40, "PAUSE" if not paused else "RESUME")
speed_up_button = Button(820, 160, 160, 40, "SPEED +")
speed_down_button = Button(820, 210, 160, 40, "SPEED -")
reset_button = Button(820, 260, 160, 40, "RESET")

# Speed slider
slider_rect = pygame.Rect(820, 320, 160, 20)
slider_knob = pygame.Rect(820 + (SIM_SPEED-1)*16, 315, 20, 30)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # Event handling
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
            
        # Button clicks
        if pause_button.is_clicked(mouse_pos, event):
            paused = not paused
            pause_button.text = "RESUME" if paused else "PAUSE"
            
        if speed_up_button.is_clicked(mouse_pos, event):
            SIM_SPEED = min(10, SIM_SPEED + 1)
            slider_knob.x = 820 + (SIM_SPEED-1)*16
            
        if speed_down_button.is_clicked(mouse_pos, event):
            SIM_SPEED = max(1, SIM_SPEED - 1)
            slider_knob.x = 820 + (SIM_SPEED-1)*16
            
        if reset_button.is_clicked(mouse_pos, event):
            for node in nodes:
                node['status'] = 'healthy'
                node['infection_timer'] = 0
                node['infection_type'] = None
            infected_nodes = random.sample(nodes, 3)
            for node in infected_nodes:
                node['status'] = 'infected'
            frame_count = 0
            day_counter = 0
            
        # Slider drag
        if event.type == MOUSEBUTTONDOWN and slider_rect.collidepoint(mouse_pos):
            if event.button == 1:  # Left mouse button
                SIM_SPEED = min(10, max(1, (mouse_pos[0] - 820) // 16 + 1))
                slider_knob.x = 820 + (SIM_SPEED-1)*16
                
        if event.type == MOUSEMOTION and event.buttons[0]:  # Left mouse drag
            if slider_rect.collidepoint(mouse_pos):
                SIM_SPEED = min(10, max(1, (mouse_pos[0] - 820) // 16 + 1))
                slider_knob.x = 820 + (SIM_SPEED-1)*16

    # Update button hover states
    pause_button.check_hover(mouse_pos)
    speed_up_button.check_hover(mouse_pos)
    speed_down_button.check_hover(mouse_pos)
    reset_button.check_hover(mouse_pos)

    # Simulation update
    if not paused:
        for _ in range(SIM_SPEED):
            frame_count += 1
            day_counter = frame_count // frames_per_day

            # Move nodes
            for node in nodes:
                pos = np.array(node['position'])
                vel = np.array(node['velocity'])

                pos += vel * SPEED
                if pos[0] < 0 or pos[0] > SIMULATION_AREA[2]:
                    vel[0] *= -1
                if pos[1] < 0 or pos[1] > SIMULATION_AREA[3]:
                    vel[1] *= -1

                node['position'] = pos
                node['velocity'] = vel

            # Spatial grid and infection logic (same as before)
            grid = {}
            for i, node in enumerate(nodes):
                key = get_grid_key(node['position'], GRID_SIZE)
                grid.setdefault(key, []).append(i)

            for key, node_indices in grid.items():
                x, y = key
                nearby_keys = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]]
                for i in node_indices:
                    node1 = nodes[i]
                    if node1['status'] != 'infected':
                        continue
                    pos1 = np.array(node1['position'])

                    for neighbor_key in nearby_keys:
                        for j in grid.get(neighbor_key, []):
                            if i == j:
                                continue
                            node2 = nodes[j]
                            if node2['status'] != 'healthy':
                                continue
                            pos2 = np.array(node2['position'])
                            if np.linalg.norm(pos1 - pos2) < INFECTION_RADIUS:
                                if random.random() < INFECTION_PROB:
                                    node2['status'] = 'infected'
                                    node2['infection_timer'] = 0
                                    node2['infection_type'] = 'symptomatic'

            for node in nodes:
                if node['status'] == 'infected':
                    node['infection_timer'] += 1
                    if node['infection_timer'] > RECOVERY_TIME:
                        node['status'] = 'recovered' if random.random() < 0.7 else 'dead'

    # Drawing
    screen.fill(BG_COLOR)
    
    # Draw simulation area
    pygame.draw.rect(screen, (40, 40, 40), SIMULATION_AREA)
    
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

    # Draw control panel
    pygame.draw.rect(screen, PANEL_COLOR, CONTROL_PANEL)
    
    # Draw title
    title_font = pygame.font.SysFont(None, 32)
    title_text = title_font.render("CONTROLS", True, TEXT_COLOR)
    screen.blit(title_text, (820, 50))
    
    # Draw buttons
    pause_button.draw(screen)
    speed_up_button.draw(screen)
    speed_down_button.draw(screen)
    reset_button.draw(screen)
    
    # Draw speed slider
    pygame.draw.rect(screen, (80, 80, 90), slider_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 150, 200), slider_knob, border_radius=5)
    
    # Draw speed value
    speed_text = font.render(f"Speed: {SIM_SPEED}x", True, TEXT_COLOR)
    screen.blit(speed_text, (820, 350))
    
    # Draw day counter
    day_text = font.render(f"Day: {day_counter}", True, TEXT_COLOR)
    screen.blit(day_text, (820, 400))
    
    # Stats
    healthy = sum(1 for n in nodes if n['status'] == 'healthy')
    infected = sum(1 for n in nodes if n['status'] == 'infected')
    recovered = sum(1 for n in nodes if n['status'] == 'recovered')
    dead = sum(1 for n in nodes if n['status'] == 'dead')
    
    stats_font = pygame.font.SysFont(None, 22)
    screen.blit(stats_font.render(f"Healthy: {healthy}", True, (0, 200, 0)), (820, 450))
    screen.blit(stats_font.render(f"Infected: {infected}", True, (255, 0, 0)), (820, 480))
    screen.blit(stats_font.render(f"Recovered: {recovered}", True, (0, 100, 255)), (820, 510))
    screen.blit(stats_font.render(f"Dead: {dead}", True, (100, 100, 100)), (820, 540))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()