import pygame
from ui.button import Button
from simulation.simulation_engine import load_network, update_positions, process_infections, update_recovery, reset_nodes
from pygame.locals import *

WIDTH, HEIGHT = 1000, 800
SIMULATION_AREA = (0, 0, 800, 800)
CONTROL_PANEL = (800, 0, 200, 800)
FPS = 30

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
        self.create_buttons()

    def create_buttons(self):
        self.pause_button = Button(820, 100, 160, 40, "PAUSE")
        self.speed_up_button = Button(820, 160, 160, 40, "SPEED +")
        self.speed_down_button = Button(820, 210, 160, 40, "SPEED -")
        self.reset_button = Button(820, 260, 160, 40, "RESET")
        self.slider_rect = pygame.Rect(820, 320, 160, 20)
        self.slider_knob = pygame.Rect(820 + (self.sim_speed - 1) * 16, 315, 20, 30)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if self.pause_button.is_clicked(mouse_pos, event):
            self.paused = not self.paused
            self.pause_button.text = "RESUME" if self.paused else "PAUSE"
        if self.speed_up_button.is_clicked(mouse_pos, event):
            self.sim_speed = min(10, self.sim_speed + 1)
            self.slider_knob.x = 820 + (self.sim_speed - 1) * 16
        if self.speed_down_button.is_clicked(mouse_pos, event):
            self.sim_speed = max(1, self.sim_speed - 1)
            self.slider_knob.x = 820 + (self.sim_speed - 1) * 16
        if self.reset_button.is_clicked(mouse_pos, event):
            self.infected_nodes = reset_nodes(self.nodes)
            self.frame_count = 0
            self.day_counter = 0
        if event.type == MOUSEBUTTONDOWN and self.slider_rect.collidepoint(mouse_pos):
            self.sim_speed = min(10, max(1, (mouse_pos[0] - 820) // 16 + 1))
            self.slider_knob.x = 820 + (self.sim_speed - 1) * 16
        if event.type == MOUSEMOTION and event.buttons[0] and self.slider_rect.collidepoint(mouse_pos):
            self.sim_speed = min(10, max(1, (mouse_pos[0] - 820) // 16 + 1))
            self.slider_knob.x = 820 + (self.sim_speed - 1) * 16

    def update(self):
        if not self.paused:
            for _ in range(self.sim_speed):
                self.frame_count += 1
                self.day_counter = self.frame_count // self.frames_per_day
                update_positions(self.nodes, SIMULATION_AREA)
                process_infections(self.nodes)
                update_recovery(self.nodes)

    def draw(self):
        self.screen.fill((30, 30, 30))
        pygame.draw.rect(self.screen, (40, 40, 40), SIMULATION_AREA)

        for node in self.nodes:
            pos = node['position']
            color = {
                'healthy': (0, 200, 0),
                'infected': (255, 0, 0),
                'recovered': (0, 100, 255),
                'dead': (100, 100, 100)
            }.get(node['status'], (255, 255, 255))
            pygame.draw.circle(self.screen, color, [int(p) for p in pos], 2)

        pygame.draw.rect(self.screen, (50, 50, 60), CONTROL_PANEL)

        for btn in [self.pause_button, self.speed_up_button, self.speed_down_button, self.reset_button]:
            btn.check_hover(pygame.mouse.get_pos())
            btn.draw(self.screen)

        pygame.draw.rect(self.screen, (80, 80, 90), self.slider_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 150, 200), self.slider_knob, border_radius=5)

        self.screen.blit(self.font.render(f"Speed: {self.sim_speed}x", True, (255, 255, 255)), (820, 350))
        self.screen.blit(self.font.render(f"Day: {self.day_counter}", True, (255, 255, 255)), (820, 400))

        stats = {
            'Healthy': sum(1 for n in self.nodes if n['status'] == 'healthy'),
            'Infected': sum(1 for n in self.nodes if n['status'] == 'infected'),
            'Recovered': sum(1 for n in self.nodes if n['status'] == 'recovered'),
            'Dead': sum(1 for n in self.nodes if n['status'] == 'dead'),
        }
        y = 450
        for label, value in stats.items():
            self.screen.blit(self.font.render(f"{label}: {value}", True, (255, 255, 255)), (820, y))
            y += 30

        pygame.display.flip()
        self.clock.tick(FPS)
