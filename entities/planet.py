import pygame
from project.model.utils import world_to_screen

class Planet:
    def __init__(self, x, y, radius, color):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.color = color

    def draw(self, screen, cam, zoom):
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, self.color, (sx, sy), int(self.radius * zoom))
