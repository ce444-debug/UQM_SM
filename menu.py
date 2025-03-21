import pygame
import sys

class MainMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font = pygame.font.SysFont("Arial", 36)
        self.options = ["New Game", "Settings", "Exit"]
        self.selected = 0

    def display(self):
        running = True
        while running:
            self.screen.fill((0, 0, 40))
            for i, option in enumerate(self.options):
                color = (255, 255, 0) if i == self.selected else (200, 200, 200)
                text = self.font.render(option, True, color)
                self.screen.blit(text, (100, 100 + i * 50))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Exit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        return self.options[self.selected]
            self.clock.tick(30)

class ModeMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font = pygame.font.SysFont("Arial", 36)
        self.options = ["Multiplayer", "Single Player", "Back"]
        self.selected = 0

    def display(self):
        running = True
        while running:
            self.screen.fill((0, 0, 40))
            title = self.font.render("Select Game Mode", True, (255, 255, 255))
            self.screen.blit(title, (100, 50))
            for i, option in enumerate(self.options):
                color = (255, 255, 0) if i == self.selected else (200, 200, 200)
                text = self.font.render(option, True, color)
                self.screen.blit(text, (100, 120 + i * 50))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Exit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        return self.options[self.selected]
            self.clock.tick(30)

class DifficultyMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font = pygame.font.SysFont("Arial", 36)
        self.options = ["Easy", "Medium", "Hard", "Back"]
        self.selected = 0

    def display(self):
        running = True
        while running:
            self.screen.fill((0, 0, 40))
            title = self.font.render("Select Difficulty", True, (255, 255, 255))
            self.screen.blit(title, (100, 50))
            for i, option in enumerate(self.options):
                color = (255, 255, 0) if i == self.selected else (200, 200, 200)
                text = self.font.render(option, True, color)
                self.screen.blit(text, (100, 120 + i * 50))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Exit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        return self.options[self.selected]
            self.clock.tick(30)

class PauseMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font = pygame.font.SysFont("Arial", 36)
        self.options = ["Resume", "Main Menu", "Exit"]
        self.selected = 0

    def display(self):
        running = True
        while running:
            self.screen.fill((0, 0, 40))
            pause_text = self.font.render("Paused", True, (255, 255, 255))
            self.screen.blit(pause_text, (100, 50))
            for i, option in enumerate(self.options):
                color = (255, 255, 0) if i == self.selected else (200, 200, 200)
                text = self.font.render(option, True, color)
                self.screen.blit(text, (100, 150 + i * 50))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Exit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        return self.options[self.selected]
            self.clock.tick(30)
