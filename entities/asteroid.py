import math
import random
import pygame
from config import FIELD_W, FIELD_H, ASTEROID_ROTATION_AXIS
from utils import wrap_delta, wrap_position, world_to_screen

class Asteroid:
    def __init__(self, x, y, radius, vx, vy, color):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.angle = random.uniform(0, 360)
        self.angular_velocity = ASTEROID_ROTATION_AXIS * random.uniform(50, 180)
        self.max_health = 5
        self.health = self.max_health
        self.active = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)
        self.angle = (self.angle + self.angular_velocity * dt) % 360

    def draw(self, screen, cam, zoom):
        ax, ay = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        half_size = self.radius * zoom
        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        corners = []
        for dx, dy in [(-half_size, -half_size), (half_size, -half_size),
                       (half_size, half_size), (-half_size, half_size)]:
            rx = dx * cos_a - dy * sin_a
            ry = dx * sin_a + dy * cos_a
            corners.append((ax + rx, ay + ry))
        pygame.draw.polygon(screen, self.color, corners)

    def take_damage(self, amount):
        self.active = False
