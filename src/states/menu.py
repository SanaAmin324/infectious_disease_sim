import pygame
import sys
from pygame import gfxdraw
import math
import random

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 24)
        self.shadow_offset = 3
        self.animation_progress = 0
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered and self.animation_progress < 10:
            self.animation_progress += 1
        elif not self.is_hovered and self.animation_progress > 0:
            self.animation_progress -= 1
            
    def draw(self, surface):
        # Animated background
        current_color = [
            self.color[i] + (self.hover_color[i]-self.color[i]) * self.animation_progress/10 
            for i in range(3)
        ]
        
        # Shadow
        shadow_rect = self.rect.move(self.shadow_offset, self.shadow_offset)
        pygame.draw.rect(surface, (50, 50, 50), shadow_rect, border_radius=8)
        
        # Main button
        pygame.draw.rect(surface, current_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)  # Border
        
        # Text
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def is_clicked(self, pos, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and 
                event.button == 1 and 
                self.rect.collidepoint(pos))

class Dropdown:
    def __init__(self, x, y, width, height, options):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected = options[0]
        self.is_open = False
        self.font = pygame.font.SysFont('Arial', 22)
        self.option_height = 35
        self.animation_height = 0
        self.max_options_visible = 4
        
    def update(self, mouse_pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                self.is_open = not self.is_open
            elif self.is_open:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(
                        self.rect.x, 
                        self.rect.y + self.rect.height + i * self.option_height,
                        self.rect.width,
                        self.option_height
                    )
                    if option_rect.collidepoint(mouse_pos):
                        self.selected = option
                        self.is_open = False
                        break
                else:
                    self.is_open = False
        
        # Animate dropdown
        if self.is_open and self.animation_height < len(self.options)*self.option_height:
            self.animation_height += 10
        elif not self.is_open and self.animation_height > 0:
            self.animation_height -= 10
            
    def draw(self, surface):
        # Main dropdown box
        pygame.draw.rect(surface, (220, 220, 230), self.rect, border_radius=5)
        pygame.draw.rect(surface, (180, 180, 190), self.rect, 2, border_radius=5)
        
        # Selected text
        text_surf = self.font.render(self.selected, True, (50, 50, 50))
        surface.blit(text_surf, (self.rect.x + 10, self.rect.y + 8))
        
        # Dropdown arrow
        arrow_points = [
            (self.rect.right - 20, self.rect.centery - 5),
            (self.rect.right - 10, self.rect.centery - 5),
            (self.rect.right - 15, self.rect.centery + 5)
        ]
        pygame.draw.polygon(surface, (100, 100, 100), arrow_points)
        
        # Options box (animated)
        if self.animation_height > 0:
            options_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y + self.rect.height,
                self.rect.width,
                min(self.animation_height, len(self.options)*self.option_height)
            )
            
            # Background
            pygame.draw.rect(surface, (240, 240, 245), options_rect, border_radius=5)
            pygame.draw.rect(surface, (200, 200, 210), options_rect, 2, border_radius=5)
            
            # Options
            visible_options = min(len(self.options), 
                                int(self.animation_height/self.option_height) + 1)
            
            for i in range(visible_options):
                option_rect = pygame.Rect(
                    self.rect.x, 
                    self.rect.y + self.rect.height + i * self.option_height,
                    self.rect.width,
                    self.option_height
                )
                
                # Highlight selected and hovered
                if self.options[i] == self.selected:
                    pygame.draw.rect(surface, (200, 230, 255), option_rect)
                elif option_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surface, (230, 230, 240), option_rect)
                
                # Option text
                text_surf = self.font.render(self.options[i], True, (50, 50, 50))
                surface.blit(text_surf, (option_rect.x + 10, option_rect.y + 8))

class MenuState:
    def __init__(self, screen, start_simulation):
        self.screen = screen
        self.start_simulation = start_simulation
        self.width, self.height = screen.get_size()

        # Colors & Fonts
        self.bg_color = (245, 248, 250)
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.subtitle_font = pygame.font.SysFont('Arial', 24)
        self.footer_font = pygame.font.SysFont('Arial', 12)

        # Dropdown with policies
        self.policies = [
            "Standard Simulation",
            "Lockdown",
            "Vaccination",
            "Restrict Gatherings",
            "Enhanced Hygiene"
        ]
        self.dropdown = Dropdown(self.width // 2 - 150, 300, 300, 40, self.policies)

        # Buttons
        self.start_button = Button(
            self.width // 2 - 100, 530, 200, 50,
            "Start Simulation", (76, 175, 80), (56, 142, 60)
        )
        self.exit_button = Button(
            self.width // 2 - 100, 600, 200, 50,
            "Exit", (244, 67, 54), (198, 40, 40)
        )

        # Logo & particles
        self.logo = self._create_logo()
        self.particles = self._create_particles()

    def _create_particles(self):
        return [
            {
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(2, 6),
                'speed': random.uniform(0.2, 0.5),
                'color': (random.randint(200, 240), random.randint(200, 240), random.randint(200, 250))
            }
            for _ in range(30)
        ]

    def _create_logo(self):
        surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(surf, (220, 240, 255, 200), (60, 60), 55)
        pygame.draw.circle(surf, (244, 67, 54, 220), (60, 60), 20)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            end_x = 60 + math.cos(rad) * 40
            end_y = 60 + math.sin(rad) * 40
            pygame.draw.line(surf, (244, 67, 54, 180), (60, 60), (end_x, end_y), 3)
        return surf

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        self.dropdown.update(mouse_pos, event)

        if self.start_button.is_clicked(mouse_pos, event):
            policy = self.dropdown.selected.lower().replace(" ", "_")
            self.start_simulation(policy)

        if self.exit_button.is_clicked(mouse_pos, event):
            pygame.quit()
            sys.exit()

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update(mouse_pos)
        self.exit_button.update(mouse_pos)

        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < -10:
                p['y'] = self.height + 10
                p['x'] = random.randint(0, self.width)

    def draw(self):
        self.screen.fill(self.bg_color)

        # Gradient background
        for y in range(0, self.height, 2):
            alpha = min(255, int(255 * (1 - y / self.height * 0.7)))
            color = (255, 255, 255, alpha)
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))

        # Particles
        for p in self.particles:
            pygame.draw.circle(self.screen, p['color'], (int(p['x']), int(p['y'])), p['size'])

        # UI Elements
        self.screen.blit(self.logo, (self.width // 2 - 60, 80))

        title_text = self.title_font.render("Disease Spread Simulator", True, (50, 50, 50))
        shadow = self.title_font.render("Disease Spread Simulator", True, (100, 100, 100))
        self.screen.blit(shadow, (self.width // 2 - title_text.get_width() // 2 + 2, 210 + 2))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 210))

        subtitle = self.subtitle_font.render("Select a scenario to simulate:", True, (100, 100, 100))
        self.screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 270))

        self.dropdown.draw(self.screen)
        self.start_button.draw(self.screen)
        self.exit_button.draw(self.screen)

        # Footer
        footer = self.footer_font.render("Epidemiology Simulation v1.0", True, (150, 150, 150))
        self.screen.blit(footer, (20, self.height - 30))

        pygame.display.flip()
