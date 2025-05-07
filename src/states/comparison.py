import pygame
from simulation.simulation_engine import *
from ui.button import Button

WIDTH, HEIGHT = 1200, 800
SIM_AREA_LEFT = (0, 0, 580, 800)
SIM_AREA_RIGHT = (600, 0, 580, 800)
CONTROL_PANEL = (1160, 0, 40, 800)
FPS = 30

class ComparisonSimulationState:
    def __init__(self, screen, policy):
        self.screen = screen
        self.policy = policy
        self.nodes1, _ = load_network("data/graphs/network.json")
        self.nodes2, _ = load_network("data/graphs/network.json")
        reset_nodes(self.nodes1)
        reset_nodes(self.nodes2)

        self.sim_speed = 1
        self.day_counter = 0
        self.frame_count = 0
        self.frames_per_day = FPS * 1
        self.paused = False
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)

        self.pause_button = Button(1000, 100, 160, 40, "PAUSE")

    def handle_event(self, event):
        pos = pygame.mouse.get_pos()
        if self.pause_button.is_clicked(pos, event):
            self.paused = not self.paused
            self.pause_button.text = "RESUME" if self.paused else "PAUSE"

    def update(self):
        if not self.paused:
            for _ in range(self.sim_speed):
                self.frame_count += 1
                if self.frame_count % self.frames_per_day == 0:
                    self.day_counter += 1
                update_positions(self.nodes1, SIM_AREA_LEFT)
                update_positions(self.nodes2, SIM_AREA_RIGHT)
                process_infections(self.nodes1)
                process_infections(self.nodes2)
                update_recovery(self.nodes1)
                update_recovery(self.nodes2)

    def draw_simulation(self, nodes, offset_x):
        for node in nodes:
            x, y = node['position']
            x += offset_x
            color = {
                'healthy': (0, 200, 0),
                'infected': (255, 0, 0),
                'recovered': (0, 100, 255),
                'dead': (100, 100, 100)
            }.get(node['status'], (255, 255, 255))
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 2)

    def draw(self):
        self.screen.fill((30, 30, 30))
        pygame.draw.rect(self.screen, (40, 40, 40), SIM_AREA_LEFT)
        pygame.draw.rect(self.screen, (40, 40, 40), SIM_AREA_RIGHT)

        self.draw_simulation(self.nodes1, 0)
        self.draw_simulation(self.nodes2, 600)

        self.pause_button.check_hover(pygame.mouse.get_pos())
        self.pause_button.draw(self.screen)

        self.screen.blit(self.font.render(f"Day: {self.day_counter}", True, (255, 255, 255)), (1000, 160))
        pygame.display.flip()
        self.clock.tick(FPS)
