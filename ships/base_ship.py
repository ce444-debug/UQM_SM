# project/ships/base_ship.py
import math
from project.config import FIELD_W, FIELD_H
from project.utils import wrap_position, wrap_delta

class BaseShip:
    next_id = 1  # Статическая переменная для уникального идентификатора

    def __init__(self, x, y, color):
        # Присваиваем уникальный ID каждому кораблю
        self.id = BaseShip.next_id
        BaseShip.next_id += 1

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
        self.radius = 15
        self.angle = 0.0  # 0° – направлен вверх
        self.spawn_timer = 1.0
        self.active_lasers = []

        # Общие параметры (будут переопределяться в наследниках)
        self.name = "BaseShip"
        self.max_crew = 10
        self.crew = 10
        self.max_energy = 10
        self.energy = 10
        self.energy_regeneration = 1
        self.energy_wait = 1.0
        self.energy_timer = self.energy_wait

        self.weapon_energy_cost = 1
        self.weapon_wait = 1.0
        self.weapon_timer = 0

        self.special_energy_cost = 1
        self.special_wait = 1.0
        self.special_timer = 0

        self.max_thrust = 20.0
        self.thrust_increment = 3.0
        self.thrust_wait = 0.1
        self.turn_speed = 90.0

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
            print(f"{self.name} (ID {self.id}) destroyed!")
            self.crew = self.max_crew

    @property
    def active(self):
        return self.crew > 0

    def fire_missile(self, enemy, game_time):
        raise NotImplementedError("fire_missile() must be implemented by subclass.")

    def fire_laser_defense(self, targets, game_time):
        raise NotImplementedError("fire_laser_defense() must be implemented by subclass.")
