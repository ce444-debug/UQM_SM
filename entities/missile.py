import math
import pygame
from config import FIELD_W, FIELD_H
from utils import wrap_delta, wrap_position

class Missile:
    def __init__(self, x, y, vx, vy, target, launch_time):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.target = target
        self.damage = 4
        self.speed = 300.0
        self.homing_strength = 2.0
        self.radius = 5
        self.launch_time = launch_time
        self.active = True

    def update(self, dt):
        if self.target is not None:
            dx = wrap_delta(self.x, self.target.x, FIELD_W)
            dy = wrap_delta(self.y, self.target.y, FIELD_H)
            distance = math.hypot(dx, dy)
            if distance != 0:
                desired_vx = self.speed * dx / distance
                desired_vy = self.speed * dy / distance
                self.vx += (desired_vx - self.vx) * self.homing_strength * dt
                self.vy += (desired_vy - self.vy) * self.homing_strength * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen, cam, zoom):
        from utils import world_to_screen
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, (255, 255, 0), (sx, sy), int(self.radius * zoom))
