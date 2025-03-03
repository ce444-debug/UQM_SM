from project.config import FIELD_W, FIELD_H
from project.utils import wrap_position, wrap_delta
from project.entities.missile import Missile
import math

class ShipA:
    def __init__(self, x, y, color):
        # Параметры корабля Earthling Cruiser
        self.name = "Earthling Cruiser"
        self.max_crew = 18
        self.crew = 18
        self.max_energy = 18
        self.energy = 18
        self.energy_regeneration = 1
        self.energy_wait = 8 / 60.0
        self.energy_timer = self.energy_wait  # Инициализация таймера энергии

        # Параметры ракетного оружия (missile launcher)
        self.weapon_energy_cost = 9
        self.weapon_wait = 10 / 60.0
        self.weapon_timer = 0

        # Параметры лазерной защиты (point-defense laser)
        self.special_energy_cost = 4
        self.special_wait = 9 / 60.0
        self.special_timer = 0

        # Параметры движения
        self.max_thrust = 24.0
        self.thrust_increment = 3.0
        self.thrust_wait = 4 / 60.0
        self.turn_speed = 180.0

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
        self.radius = 15
        self.angle = 0.0  # 0° – направление вверх
        self.spawn_timer = 1.0

        # Список активных лазерных лучей (для визуализации)
        self.active_lasers = []

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)
        if self.spawn_timer > 0:
            self.spawn_timer = max(0, self.spawn_timer - dt)
        self.energy_timer -= dt
        if self.energy_timer <= 0:
            if self.energy < self.max_energy:
                self.energy = min(self.max_energy, self.energy + self.energy_regeneration)
            self.energy_timer = self.energy_wait
        if self.weapon_timer > 0:
            self.weapon_timer -= dt
        if self.special_timer > 0:
            self.special_timer -= dt
        new_lasers = []
        for (tx, ty, t) in self.active_lasers:
            t -= dt
            if t > 0:
                new_lasers.append((tx, ty, t))
        self.active_lasers = new_lasers

    def take_damage(self, amount):
        self.crew -= amount
        if self.crew <= 0:
            print(f"{self.name} destroyed!")
            self.crew = self.max_crew

    def fire_missile(self, enemy, game_time):
        if self.weapon_timer <= 0 and self.energy >= self.weapon_energy_cost:
            self.energy -= self.weapon_energy_cost
            if self.energy == self.max_energy:
                self.weapon_timer = self.weapon_wait / 2
            else:
                self.weapon_timer = self.weapon_wait
            rad = math.radians(self.angle)
            front_x = self.x + self.radius * math.sin(rad)
            front_y = self.y - self.radius * math.cos(rad)
            missile_vx = self.vx + 50 * math.sin(rad)
            missile_vy = self.vy - 50 * math.cos(rad)
            return Missile(front_x, front_y, missile_vx, missile_vy, enemy, game_time)
        return None

    def fire_laser_defense(self, targets, game_time):
        laser_range = self.radius * 2.2 * 2  # приблизительно чуть более 2× длины корабля
        valid_targets = []
        for target in targets:
            dx = wrap_delta(self.x, target.x, FIELD_W)
            dy = wrap_delta(self.y, target.y, FIELD_H)
            effective_distance = math.hypot(dx, dy) - target.radius
            if effective_distance <= laser_range:
                valid_targets.append(target)
        if not valid_targets or self.special_timer > 0 or self.energy < self.special_energy_cost:
            return
        self.energy -= self.special_energy_cost
        if self.energy == self.max_energy:
            self.special_timer = self.special_wait / 5
        else:
            self.special_timer = self.special_wait
        for target in valid_targets:
            self.active_lasers.append((target.x, target.y, 0.1))
            if hasattr(target, 'launch_time'):
                if target.launch_time < game_time:
                    target.active = False
            else:
                target.take_damage(1)
