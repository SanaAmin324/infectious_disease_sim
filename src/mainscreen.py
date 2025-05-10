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
        # All scenarios will use StandardSimulationState but with different parameters
        self.current = StandardSimulationState(self.screen, policy)

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

    # Use pygame.RESIZABLE to allow resizing
    screen = pygame.display.set_mode((1000, 800), pygame.RESIZABLE)
    pygame.display.set_caption("Disease Simulation")

    manager = StateManager(screen)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:  # Handle window resizing
                # Update screen size when resized
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                manager.screen = screen  # Update manager screen reference to new size
            manager.handle_event(event)

        manager.update()
        manager.draw()

        pygame.display.flip()  # Make sure to flip the screen to update

    pygame.quit()

if __name__ == "__main__":
    main()
