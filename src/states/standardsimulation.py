import pygame
import numpy as np
import random
import matplotlib.pyplot as plt
import csv
from ui.button import Button
from simulation.simulation_engine import load_network, update_positions, process_infections, update_recovery, reset_nodes
from pygame.locals import *
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Constants
DEFAULT_WIDTH, DEFAULT_HEIGHT = 1000, 800
SIMULATION_AREA_RATIO = 0.8
CONTROL_PANEL_RATIO = 0.2
FPS = 30
NODE_RADIUS = 2
INFECTION_RADIUS = 10
INFECTION_PROB = 0.2
RECOVERY_TIME = 600
SPEED = 1.5

# Colors
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (50, 50, 60)
BUTTON_COLOR = (70, 70, 80)
BUTTON_HOVER = (90, 90, 100)
TEXT_COLOR = (255, 255, 255)

class StandardSimulationState:
    def __init__(self, screen):
        self.screen = screen
        self.nodes, self.edges = load_network("data/graphs/network.json")
        self.infected_nodes = reset_nodes(self.nodes)
        self.paused = False
        self.frame_count = 0
        self.day_counter = 0
        self.frames_per_day = FPS * 1
        self.sim_speed = 1
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        
        # For statistics tracking
        self.healthy_data = []
        self.infected_data = []
        self.recovered_data = []
        self.dead_data = []
        
        # Setup matplotlib graph
        self.fig, self.ax = plt.subplots(figsize=(2, 1.5))
        self.canvas = FigureCanvas(self.fig)
        
        self.create_buttons()
        self.update_simulation_dimensions()

    def update_simulation_dimensions(self):
        screen_width, screen_height = self.screen.get_size()
        self.simulation_width = int(screen_width * SIMULATION_AREA_RATIO)
        self.control_panel_width = screen_width - self.simulation_width
        self.SIMULATION_AREA = (0, 0, self.simulation_width, screen_height)
        self.CONTROL_PANEL = (self.simulation_width, 0, self.control_panel_width, screen_height)
        self.create_buttons()

    def create_buttons(self):
        screen_width, screen_height = self.screen.get_size()
        simulation_width = int(screen_width * SIMULATION_AREA_RATIO)
        control_width = screen_width - simulation_width
        
        button_width = min(200, control_width - 20)
        
        self.pause_button = Button(simulation_width + 10, 100, button_width, 40, "PAUSE")
        self.speed_up_button = Button(simulation_width + 10, 160, button_width, 40, "SPEED +")
        self.speed_down_button = Button(simulation_width + 10, 210, button_width, 40, "SPEED -")
        self.reset_button = Button(simulation_width + 10, 260, button_width, 40, "RESET")
        self.export_button = Button(simulation_width + 10, 310, button_width, 40, "EXPORT CSV")
        
        self.slider_rect = pygame.Rect(simulation_width + 10, 420, button_width, 20)
        self.slider_knob = pygame.Rect(self.slider_rect.x + (self.sim_speed - 1) * (button_width // 10), 415, 20, 30)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == VIDEORESIZE:
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self.update_simulation_dimensions()
        
        if self.pause_button.is_clicked(mouse_pos, event):
            self.paused = not self.paused
            self.pause_button.text = "RESUME" if self.paused else "PAUSE"
            
        if self.speed_up_button.is_clicked(mouse_pos, event):
            self.sim_speed = min(10, self.sim_speed + 1)
            self.slider_knob.x = self.slider_rect.x + (self.sim_speed - 1) * (self.slider_rect.width // 10)
            
        if self.speed_down_button.is_clicked(mouse_pos, event):
            self.sim_speed = max(1, self.sim_speed - 1)
            self.slider_knob.x = self.slider_rect.x + (self.sim_speed - 1) * (self.slider_rect.width // 10)
            
        if self.reset_button.is_clicked(mouse_pos, event):
            self.infected_nodes = reset_nodes(self.nodes)
            self.healthy_data.clear()
            self.infected_data.clear()
            self.recovered_data.clear()
            self.dead_data.clear()
            self.frame_count = 0
            self.day_counter = 0
            
        if self.export_button.is_clicked(mouse_pos, event):
            self.export_to_csv()
            
        if event.type == MOUSEBUTTONDOWN and self.slider_rect.collidepoint(mouse_pos):
            self.sim_speed = min(10, max(1, (mouse_pos[0] - self.slider_rect.x) // (self.slider_rect.width // 10) + 1))
            self.slider_knob.x = self.slider_rect.x + (self.sim_speed - 1) * (self.slider_rect.width // 10)
            
        if event.type == MOUSEMOTION and event.buttons[0] and self.slider_rect.collidepoint(mouse_pos):
            self.sim_speed = min(10, max(1, (mouse_pos[0] - self.slider_rect.x) // (self.slider_rect.width // 10) + 1))
            self.slider_knob.x = self.slider_rect.x + (self.sim_speed - 1) * (self.slider_rect.width // 10)

    def update(self):
        if not self.paused:
            for _ in range(self.sim_speed):
                self.frame_count += 1
                self.day_counter = self.frame_count // self.frames_per_day
                update_positions(self.nodes, self.SIMULATION_AREA)
                process_infections(self.nodes)
                update_recovery(self.nodes)
                
                # Update statistics
                self.healthy_data.append(sum(1 for n in self.nodes if n['status'] == 'healthy'))
                self.infected_data.append(sum(1 for n in self.nodes if n['status'] == 'infected'))
                self.recovered_data.append(sum(1 for n in self.nodes if n['status'] == 'recovered'))
                self.dead_data.append(sum(1 for n in self.nodes if n['status'] == 'dead'))

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Draw simulation area
        pygame.draw.rect(self.screen, (40, 40, 40), self.SIMULATION_AREA)
        for node in self.nodes:
            pos = node['position']
            color = {
                'healthy': (0, 200, 0),
                'infected': (255, 0, 0),
                'recovered': (0, 100, 255),
                'dead': (100, 100, 100)
            }.get(node['status'], (255, 255, 255))
            pygame.draw.circle(self.screen, color, [int(p) for p in pos], NODE_RADIUS)
        
        # Draw control panel
        pygame.draw.rect(self.screen, PANEL_COLOR, self.CONTROL_PANEL)
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in [self.pause_button, self.speed_up_button, self.speed_down_button, 
                   self.reset_button, self.export_button]:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)
        
        # Draw speed slider
        pygame.draw.rect(self.screen, (120, 120, 140), self.slider_rect)
        pygame.draw.rect(self.screen, (200, 200, 220), self.slider_knob, border_radius=5)
        
        # Draw stats text
        self.screen.blit(self.font.render(f"Speed: {self.sim_speed}x", True, TEXT_COLOR), 
                         (self.simulation_width + 10, 450))
        self.screen.blit(self.font.render(f"Day: {self.day_counter}", True, TEXT_COLOR), 
                         (self.simulation_width + 10, 480))
        
        # Draw current stats
        stats = {
            'Healthy': self.healthy_data[-1] if self.healthy_data else 0,
            'Infected': self.infected_data[-1] if self.infected_data else 0,
            'Recovered': self.recovered_data[-1] if self.recovered_data else 0,
            'Dead': self.dead_data[-1] if self.dead_data else 0,
        }
        y = 510
        for label, value in stats.items():
            self.screen.blit(self.font.render(f"{label}: {value}", True, TEXT_COLOR), 
                            (self.simulation_width + 10, y))
            y += 30
        
        # Draw the graph
        self.draw_statistics_graph()
        
        pygame.display.flip()
        self.clock.tick(FPS)

    def draw_statistics_graph(self):
        self.ax.clear()
        if len(self.healthy_data) > 0:
            self.ax.plot(self.healthy_data, label='Healthy', color='green')
            self.ax.plot(self.infected_data, label='Infected', color='red')
            self.ax.plot(self.recovered_data, label='Recovered', color='blue')
            self.ax.plot(self.dead_data, label='Dead', color='gray')
            self.ax.set_title('Population Stats', fontsize=8)
            self.ax.set_xlabel('Time', fontsize=6)
            self.ax.set_ylabel('Count', fontsize=6)
            self.ax.legend(fontsize=6, loc='upper right')
            self.ax.tick_params(labelsize=6)
            
            self.canvas.draw()
            renderer = self.canvas.get_renderer()
            raw_data = renderer.buffer_rgba()
            size = self.canvas.get_width_height()
            graph_surface = pygame.image.frombuffer(raw_data, size, "RGBA")
            
            # Calculate graph dimensions based on available space
            graph_height = min(300, self.screen.get_height() - 550)
            graph_width = min(300, self.control_panel_width - 20)
            
            graph_surface = pygame.transform.scale(graph_surface, 
                                                (graph_width, graph_height))
            
            self.screen.blit(graph_surface, 
                           (self.simulation_width + 10, 
                            self.screen.get_height() - graph_height - 20))

    def export_to_csv(self):
        with open("simulation_data.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Time", "Healthy", "Infected", "Recovered", "Dead"])
            for t in range(len(self.healthy_data)):
                writer.writerow([
                    t,
                    self.healthy_data[t],
                    self.infected_data[t],
                    self.recovered_data[t],
                    self.dead_data[t]
                ])
