import pygame
import numpy as np
import random
import matplotlib.pyplot as plt
import csv
from ui.button import Button
from simulation.simulation_engine import load_network, update_positions, process_infections, update_recovery, reset_nodes
from pygame.locals import *
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from states.no_measures_simulation import NoMeasuresSimulation
from states.social_distancing_simulation import SocialDistancingSimulation
from states.mask_wearing_simulation import MaskWearingSimulation
from states.vaccination_simulation import VaccinationSimulation
from states.lockdown_simulation import LockdownSimulation

# Constants
DEFAULT_WIDTH, DEFAULT_HEIGHT = 1000, 800
SIMULATION_AREA_RATIO = 0.8
CONTROL_PANEL_RATIO = 0.2
FPS = 30
NODE_RADIUS = 3

# Colors
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (50, 50, 60)
BUTTON_COLOR = (70, 70, 80)
BUTTON_HOVER = (90, 90, 100)
TEXT_COLOR = (255, 255, 255)
DROPDOWN_COLOR = (60, 60, 70)
DROPDOWN_HOVER = (80, 80, 90)
STATS_COLOR = (200, 200, 200)

class StandardSimulationState:
    def __init__(self, screen, policy="standard_simulation"):
        self.screen = screen
        self.policy = policy.replace("_", " ").title()
        
        # Initialize scenario-specific simulation
        if self.policy == "Standard Simulation":
            self.current_scenario = "Standard"
            # Create a custom simulation for standard scenario
            self.simulation = NoMeasuresSimulation(screen, "Standard")  # Pass scenario name
            # Modify parameters for standard simulation
            self.simulation.INFECTION_RADIUS = 15  # Slightly reduced from No Measures
            self.simulation.INFECTION_PROB = 0.25  # Slightly reduced from No Measures
            self.simulation.RECOVERY_TIME = 800    # Longer recovery time
            self.simulation.SPEED = 1.5           # Moderate speed
            # Add basic precautions
            self.simulation.BASIC_PRECAUTIONS = True
            self.simulation.PRECAUTION_FACTOR = 0.2  # 20% reduction in infection probability
        elif self.policy == "Social Distancing":
            self.current_scenario = "Social Distancing"
            self.simulation = SocialDistancingSimulation(screen)
        elif self.policy == "Mask Wearing":
            self.current_scenario = "Mask Wearing"
            self.simulation = MaskWearingSimulation(screen)
        elif self.policy == "Vaccination":
            self.current_scenario = "Vaccination"
            self.simulation = VaccinationSimulation(screen)
        elif self.policy == "Lockdown":
            self.current_scenario = "Lockdown"
            self.simulation = LockdownSimulation(screen)
        else:
            self.current_scenario = "No Measures"
            self.simulation = NoMeasuresSimulation(screen, "No Measures")  # Pass scenario name
        
        self.paused = False
        self.scenario_dropdown_open = False
        self.scenario_options = ["Standard", "No Measures", "Social Distancing", "Mask Wearing", "Vaccination", "Lockdown"]
        
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
        
        # Create scenario dropdown button
        self.scenario_button = Button(simulation_width + 10, 50, button_width, 40, self.current_scenario)
        
        # Create control buttons with proper spacing
        self.pause_button = Button(simulation_width + 10, 100, button_width, 40, "PAUSE")
        self.speed_up_button = Button(simulation_width + 10, 150, button_width, 40, "SPEED +")
        self.speed_down_button = Button(simulation_width + 10, 200, button_width, 40, "SPEED -")
        self.reset_button = Button(simulation_width + 10, 250, button_width, 40, "RESET")
        self.export_button = Button(simulation_width + 10, 300, button_width, 40, "EXPORT DATA")
        
        # Create speed slider
        self.slider_rect = pygame.Rect(simulation_width + 10, 350, button_width, 20)
        self.slider_knob = pygame.Rect(self.slider_rect.x + (self.simulation.sim_speed - 1) * (button_width // 10), 
                                     345, 20, 30)
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == VIDEORESIZE:
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self.update_simulation_dimensions()
        
        # Handle scenario dropdown
        if self.scenario_button.is_clicked(mouse_pos, event):
            self.scenario_dropdown_open = not self.scenario_dropdown_open
        
        if self.scenario_dropdown_open and event.type == MOUSEBUTTONDOWN:
            dropdown_y = 90
            for scenario in self.scenario_options:
                scenario_rect = pygame.Rect(self.scenario_button.rect.x, dropdown_y, 
                                         self.scenario_button.rect.width, 30)
                if scenario_rect.collidepoint(mouse_pos):
                    self.current_scenario = scenario
                    self.scenario_button.text = scenario
                    self.scenario_dropdown_open = False
                    
                    # Create new simulation instance for selected scenario
                    if scenario == "Standard":
                        self.simulation = NoMeasuresSimulation(self.screen, "Standard")
                        # Modify parameters for standard simulation
                        self.simulation.INFECTION_RADIUS = 15
                        self.simulation.INFECTION_PROB = 0.25
                        self.simulation.RECOVERY_TIME = 800
                        self.simulation.SPEED = 1.5
                        self.simulation.BASIC_PRECAUTIONS = True
                        self.simulation.PRECAUTION_FACTOR = 0.2
                    elif scenario == "No Measures":
                        self.simulation = NoMeasuresSimulation(self.screen, "No Measures")
                    elif scenario == "Social Distancing":
                        self.simulation = SocialDistancingSimulation(self.screen)
                    elif scenario == "Mask Wearing":
                        self.simulation = MaskWearingSimulation(self.screen)
                    elif scenario == "Vaccination":
                        self.simulation = VaccinationSimulation(self.screen)
                    elif scenario == "Lockdown":
                        self.simulation = LockdownSimulation(self.screen)
                    break
                dropdown_y += 30
        
        if self.pause_button.is_clicked(mouse_pos, event):
            self.paused = not self.paused
            self.simulation.paused = self.paused
            self.pause_button.text = "RESUME" if self.paused else "PAUSE"
            
        if self.speed_up_button.is_clicked(mouse_pos, event):
            self.simulation.sim_speed = min(10, self.simulation.sim_speed + 1)
            self.slider_knob.x = self.slider_rect.x + (self.simulation.sim_speed - 1) * (self.slider_rect.width // 10)
            
        if self.speed_down_button.is_clicked(mouse_pos, event):
            self.simulation.sim_speed = max(1, self.simulation.sim_speed - 1)
            self.slider_knob.x = self.slider_rect.x + (self.simulation.sim_speed - 1) * (self.slider_rect.width // 10)
            
        if self.reset_button.is_clicked(mouse_pos, event):
            # Reset current simulation
            if self.current_scenario == "No Measures":
                self.simulation = NoMeasuresSimulation(self.screen)
            elif self.current_scenario == "Social Distancing":
                self.simulation = SocialDistancingSimulation(self.screen)
            elif self.current_scenario == "Mask Wearing":
                self.simulation = MaskWearingSimulation(self.screen)
            elif self.current_scenario == "Vaccination":
                self.simulation = VaccinationSimulation(self.screen)
            elif self.current_scenario == "Lockdown":
                self.simulation = LockdownSimulation(self.screen)
            
        if self.export_button.is_clicked(mouse_pos, event):
            self.export_to_csv()
            
        if event.type == MOUSEBUTTONDOWN and self.slider_rect.collidepoint(mouse_pos):
            self.simulation.sim_speed = min(10, max(1, (mouse_pos[0] - self.slider_rect.x) // (self.slider_rect.width // 10) + 1))
            self.slider_knob.x = self.slider_rect.x + (self.simulation.sim_speed - 1) * (self.slider_rect.width // 10)
            
        if event.type == MOUSEMOTION and event.buttons[0] and self.slider_rect.collidepoint(mouse_pos):
            self.simulation.sim_speed = min(10, max(1, (mouse_pos[0] - self.slider_rect.x) // (self.slider_rect.width // 10) + 1))
            self.slider_knob.x = self.slider_rect.x + (self.simulation.sim_speed - 1) * (self.slider_rect.width // 10)
    
    def update(self):
        self.simulation.update()
    
    def draw(self):
        # Clear the entire screen first
        self.screen.fill(BG_COLOR)
        
        # Draw simulation
        self.simulation.draw()
        
        # Draw control panel
        pygame.draw.rect(self.screen, PANEL_COLOR, self.CONTROL_PANEL)
        
        # Draw scenario dropdown
        self.scenario_button.draw(self.screen)
        if self.scenario_dropdown_open:
            dropdown_y = 90
            for scenario in self.scenario_options:
                scenario_rect = pygame.Rect(self.scenario_button.rect.x, dropdown_y, 
                                         self.scenario_button.rect.width, 30)
                color = DROPDOWN_HOVER if scenario_rect.collidepoint(pygame.mouse.get_pos()) else DROPDOWN_COLOR
                pygame.draw.rect(self.screen, color, scenario_rect)
                self.screen.blit(self.simulation.font.render(scenario, True, TEXT_COLOR), 
                               (scenario_rect.x + 5, scenario_rect.y + 5))
                dropdown_y += 30
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in [self.pause_button, self.speed_up_button, self.speed_down_button, 
                   self.reset_button, self.export_button]:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)
        
        # Draw speed slider
        pygame.draw.rect(self.screen, (120, 120, 140), self.slider_rect)
        pygame.draw.rect(self.screen, (200, 200, 220), self.slider_knob, border_radius=5)
        
        # Draw speed value
        speed_text = self.simulation.font.render(f"Speed: {self.simulation.sim_speed}x", True, TEXT_COLOR)
        self.screen.blit(speed_text, (self.slider_rect.x, self.slider_rect.y + 25))
        
        # Draw the graph
        self.draw_statistics_graph()
        
        # Single display flip at the end
        pygame.display.flip()
        self.simulation.clock.tick(FPS)
    
    def draw_statistics_graph(self):
        self.ax.clear()
        if len(self.simulation.healthy_data) > 0:
            self.ax.plot(self.simulation.healthy_data, label='Healthy', color='green')
            self.ax.plot(self.simulation.infected_data, label='Infected', color='red')
            self.ax.plot(self.simulation.recovered_data, label='Recovered', color='blue')
            self.ax.plot(self.simulation.dead_data, label='Dead', color='gray')
            self.ax.set_title('Population Stats Over Time', fontsize=8)
            self.ax.set_xlabel('Days', fontsize=6)
            self.ax.set_ylabel('Count', fontsize=6)
            self.ax.legend(fontsize=6, loc='upper right')
            self.ax.tick_params(labelsize=6)
            
            self.canvas.draw()
            renderer = self.canvas.get_renderer()
            raw_data = renderer.buffer_rgba()
            size = self.canvas.get_width_height()
            graph_surface = pygame.image.frombuffer(raw_data, size, "RGBA")
            
            # Calculate graph dimensions based on available space
            graph_height = min(300, self.screen.get_height() - 400)
            graph_width = min(300, self.control_panel_width - 20)
            
            graph_surface = pygame.transform.scale(graph_surface, 
                                                (graph_width, graph_height))
            
            self.screen.blit(graph_surface, 
                           (self.simulation_width + 10, 
                            self.screen.get_height() - graph_height - 20))
    
    def export_to_csv(self):
        try:
            # Get the user's Documents folder path
            import os
            from pathlib import Path
            documents_path = str(Path.home() / "Documents")
            
            # Create a timestamp for unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_data_{timestamp}.xlsx"
            full_path = os.path.join(documents_path, filename)
            
            # Create Excel file using pandas
            import pandas as pd
            
            # Create DataFrame
            data = {
                'Time': range(len(self.simulation.healthy_data)),
                'Healthy': self.simulation.healthy_data,
                'Infected': self.simulation.infected_data,
                'Recovered': self.simulation.recovered_data,
                'Dead': self.simulation.dead_data
            }
            df = pd.DataFrame(data)
            
            # Save as Excel file
            df.to_excel(full_path, index=False, engine='openpyxl')
            
            # Show success message
            print(f"Data successfully exported to {full_path}")
            
            # Create a temporary message on screen
            font = pygame.font.SysFont(None, 24)
            text = font.render(f"Exported to Documents/{filename}", True, (0, 255, 0))
            text_rect = text.get_rect(center=(self.simulation_width + self.control_panel_width//2, 360))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            
            # Wait for 2 seconds to show the message
            pygame.time.wait(2000)
            
            # Try to open the file with the default application (Excel)
            try:
                os.startfile(full_path)
            except:
                print("Could not automatically open the file")
            
        except PermissionError:
            print("Permission denied: Cannot write to file")
            # Show error message
            font = pygame.font.SysFont(None, 24)
            text = font.render("Error: Permission denied", True, (255, 0, 0))
            text_rect = text.get_rect(center=(self.simulation_width + self.control_panel_width//2, 360))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(2000)
            
        except Exception as e:
            print(f"Error exporting data: {str(e)}")
            # Show error message
            font = pygame.font.SysFont(None, 24)
            text = font.render(f"Error: {str(e)}", True, (255, 0, 0))
            text_rect = text.get_rect(center=(self.simulation_width + self.control_panel_width//2, 360))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(2000)
