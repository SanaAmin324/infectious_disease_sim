import pygame
from states.menu import MenuState
from states.standardsimulation import StandardSimulationState
from states.comparison import ComparisonSimulationState

class StateManager:
    def __init__(self, screen):
        self.screen = screen
        self.states = {}
        self.current = MenuState(screen, self.start_simulation)

    def start_simulation(self, policy):
        if policy == "standard_simulation":
            self.current = StandardSimulationState(self.screen)
        else:
            self.current = ComparisonSimulationState(self.screen, policy)

    def handle_event(self, event):
     result = self.current.handle_event(event)
     if result == "menu":
        self.current = MenuState(self.screen, self.start_simulation)


    def update(self):
        self.current.update()

    def draw(self):
        self.current.draw()

def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 800))
    pygame.display.set_caption("Disease Simulation")

    manager = StateManager(screen)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            manager.handle_event(event)

        manager.update()
        manager.draw()

    pygame.quit()

if __name__ == "__main__":
    main()
