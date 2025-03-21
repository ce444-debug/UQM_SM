import math
from project.config import FIELD_W, FIELD_H
from project.utils import wrap_position, wrap_delta
import pygame
from project.entities.projectile import Projectile

class Missile(Projectile):
    def __init__(self, x, y, vx, vy, target, launch_time):
        # Наследуем общие поля: damage=4, radius=5
        super().__init__(x, y, vx, vy, damage=4, radius=5)
        self.target = target
        self.speed = 300.0
        self.homing_strength = 2.0
        self.launch_time = launch_time
        self.lifetime = 3.0  # Время жизни снаряда (секунд)

    def update(self, dt):
        # Уменьшаем время жизни
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return

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
        # Рисуем ракету желтым цветом
        super().draw(screen, cam, zoom, color=(255, 255, 0))
