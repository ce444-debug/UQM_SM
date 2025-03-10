# project/entities/mine.py
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
        self.speed = 200.0         # базовая скорость для режима homing
        self.homing_strength = 1.0   # коэффициент корректировки скорости в режиме homing
        self.radius = 5
        self.launch_time = launch_time
        self.active = True
        self.launching = launching   # True, пока мина находится в режиме запуска

    def update(self, dt):
        if self.launching:
            # Пока мина находится в режиме запуска, она летит по зафиксированной начальной скорости,
            # независимо от движения корабля, который её запустил.
            self.x += self.vx * dt
            self.y += self.vy * dt
        else:
            # После фиксации мина может войти в режим homing, если цель задана и активна.
            if self.target is not None and getattr(self.target, 'active', True):
                dx = wrap_delta(self.x, self.target.x, FIELD_W)
                dy = wrap_delta(self.y, self.target.y, FIELD_H)
                distance = math.hypot(dx, dy)
                tracking_range = 24 * self.radius  # 12 mine-diameters
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
        from project.utils import world_to_screen
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, (255, 0, 0), (sx, sy), int(self.radius * zoom))


class Plasmoid:
    RING_SCALING = 1.5  # Множитель для увеличения радиуса кольца
    def __init__(self, orbit_angle, ring_start_time, orbit_speed=50.0, lifetime=1.0):
        """
        Создает элемент плазмоидного кольца.
        orbit_angle: угол (в радианах) относительно центра владельца.
        ring_start_time: время запуска кольца (общий для всех элементов).
        orbit_speed: скорость расширения кольца.
        lifetime: время жизни плазмоида.
        """
        self.owner = None  # Будет установлен владельцем при создании кольца
        self.orbit_angle = orbit_angle
        self.ring_start_time = ring_start_time
        self.orbit_speed = orbit_speed
        self.base_radius = 4      # базовый радиус плазмоида
        self.radius = self.base_radius
        self.damage = 3         # наносит 3 единицы урона
        self.active = True
        self.lifetime = lifetime
        self.x = 0.0
        self.y = 0.0

    def update(self, dt, game_time):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return
        # Вычисляем текущее расстояние от владельца с учетом множителя RING_SCALING
        orbit_distance = Plasmoid.RING_SCALING * (game_time - self.ring_start_time) * self.orbit_speed
        if self.owner is not None:
            self.x = self.owner.x + orbit_distance * math.sin(self.orbit_angle)
            self.y = self.owner.y - orbit_distance * math.cos(self.orbit_angle)
        else:
            self.x += self.orbit_speed * dt * math.sin(self.orbit_angle)
            self.y -= self.orbit_speed * dt * math.cos(self.orbit_angle)
        # Увеличиваем радиус плазмоида пропорционально orbit_distance
        self.radius = self.base_radius + orbit_distance / 50.0
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen, cam, zoom):
        from project.utils import world_to_screen
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, (0, 255, 255), (sx, sy), int(self.radius * zoom))
