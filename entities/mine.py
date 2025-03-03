import math
from project.config import FIELD_W, FIELD_H
from project.utils import wrap_position, wrap_delta
import pygame

class Mine:
    def __init__(self, x, y, vx, vy, target, launch_time, launching=True):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.target = target
        self.damage = 4
        self.speed = 200.0  # можно настроить
        self.homing_strength = 1.0  # сила гоминга после размещения
        self.radius = 5
        self.launch_time = launch_time
        self.active = True
        self.launching = launching  # True, если находится в фазе запуска

    def update(self, dt):
        current_time = pygame.time.get_ticks() / 1000.0
        if self.launching:
            if current_time - self.launch_time > 0.5:
                self.launching = False
        else:
            if self.target is not None:
                dx = self.target.x - self.x
                dy = self.target.y - self.y
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
        from project.utils import world_to_screen
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, (255, 0, 0), (sx, sy), int(self.radius * zoom))


class Plasmoid:
    def __init__(self, x, y, vx, vy, launch_time):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = 3
        self.radius = 4
        self.launch_time = launch_time
        self.active = True
        self.lifetime = 1.0  # Время жизни плазмоида (в секундах)
        self.owner = None  # Будет установлен в момент создания

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen, cam, zoom):
        from project.utils import world_to_screen
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        # Цвет плазмоида можно изменить, например, на голубой
        pygame.draw.circle(screen, (0, 255, 255), (sx, sy), int(self.radius * zoom))
