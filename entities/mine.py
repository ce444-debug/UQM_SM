import math
from project.config import FIELD_W, FIELD_H
from project.utils import wrap_position, wrap_delta
import pygame
from project.entities.projectile import Projectile

class Mine(Projectile):
    def __init__(self, x, y, vx, vy, target, launch_time, launching=True):
        # Наследуем общие поля: damage=4, radius=5
        super().__init__(x, y, vx, vy, damage=4, radius=5)
        self.target = target
        self.speed = 200.0         # Базовая скорость для режима homing
        self.homing_strength = 1.0   # Коэффициент корректировки скорости в режиме homing
        self.launch_time = launch_time
        self.launching = launching   # True, пока мина находится в режиме запуска

    def update(self, dt):
        if self.launching:
            # В режиме запуска мина просто движется по фиксированной скорости
            self.x += self.vx * dt
            self.y += self.vy * dt
        else:
            # После фиксации мина может войти в режим homing, если цель активна
            if self.target is not None and getattr(self.target, 'active', True):
                dx = wrap_delta(self.x, self.target.x, FIELD_W)
                dy = wrap_delta(self.y, self.target.y, FIELD_H)
                distance = math.hypot(dx, dy)
                tracking_range = 24 * self.radius  # Диапазон отслеживания
                if distance <= tracking_range and distance != 0:
                    desired_vx = self.speed * dx / distance
                    desired_vy = self.speed * dy / distance
                    self.vx += (desired_vx - self.vx) * self.homing_strength * dt
                    self.vy += (desired_vy - self.vy) * self.homing_strength * dt
                else:
                    self.vx = 0
                    self.vy = 0
            else:
                self.vx = 0
                self.vy = 0
            self.x += self.vx * dt
            self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen, cam, zoom):
        # Рисуем мину красным цветом
        super().draw(screen, cam, zoom, color=(255, 0, 0))


class Plasmoid(Projectile):
    RING_SCALING = 1.5  # Множитель для увеличения радиуса кольца
    def __init__(self, orbit_angle, ring_start_time, orbit_speed=50.0, lifetime=1.0):
        # Изначально позиция и скорость неизвестны, поэтому задаём (0,0)
        super().__init__(0, 0, 0, 0, damage=3, radius=4)
        self.owner = None  # Будет установлен владельцем при создании кольца
        self.orbit_angle = orbit_angle
        self.ring_start_time = ring_start_time
        self.orbit_speed = orbit_speed
        self.base_radius = 4      # Базовый радиус плазмоида
        self.radius = self.base_radius
        self.lifetime = lifetime

    def update(self, dt, game_time):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return
        orbit_distance = Plasmoid.RING_SCALING * (game_time - self.ring_start_time) * self.orbit_speed
        if self.owner is not None:
            self.x = self.owner.x + orbit_distance * math.sin(self.orbit_angle)
            self.y = self.owner.y - orbit_distance * math.cos(self.orbit_angle)
        else:
            self.x += self.orbit_speed * dt * math.sin(self.orbit_angle)
            self.y -= self.orbit_speed * dt * math.cos(self.orbit_angle)
        self.radius = self.base_radius + orbit_distance / 50.0
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen, cam, zoom):
        # Рисуем плазмоид голубым цветом
        super().draw(screen, cam, zoom, color=(0, 255, 255))
