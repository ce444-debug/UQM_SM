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

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen, cam, zoom):
        from project.utils import world_to_screen
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, (0, 255, 255), (sx, sy), int(self.radius * zoom))


class ShipB:
    def __init__(self, x, y, color):
        # Параметры корабля KOHR-AH MARAUDER
        self.name = "KOHR-AH MARAUDER"
        self.max_crew = 42
        self.crew = 42
        self.max_energy = 42
        self.energy = 42
        self.energy_regeneration = 1
        self.energy_wait = 4 / 60.0
        self.energy_timer = self.energy_wait  # Инициализация таймера энергии

        # Параметры мин (mine launcher)
        self.weapon_energy_cost = 6
        self.weapon_wait = 6 / 60.0
        self.weapon_timer = 0

        # Параметры плазмоида (plasmoid ring)
        self.special_energy_cost = 21
        self.special_wait = 9 / 60.0
        self.special_timer = 0

        # Параметры движения
        self.max_thrust = 30.0
        self.thrust_increment = 3.0
        self.thrust_wait = 4 / 60.0
        self.turn_speed = 90.0

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
        self.radius = 15
        self.angle = 0.0
        self.spawn_timer = 1.0

        # Список уже размещённых мин (максимум 8)
        self.deployed_mines = []
        # Добавляем пустой список для совместимости с основным циклом (laser rendering)
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

    def take_damage(self, amount):
        self.crew -= amount
        if self.crew <= 0:
            print(f"{self.name} destroyed!")
            self.crew = self.max_crew

    def fire_mine(self, enemy, game_time):
        if self.weapon_timer <= 0 and self.energy >= self.weapon_energy_cost:
            self.energy -= self.weapon_energy_cost
            if self.energy == self.max_energy:
                self.weapon_timer = self.weapon_wait / 2
            else:
                self.weapon_timer = self.weapon_wait
            rad = math.radians(self.angle)
            front_x = self.x + self.radius * math.sin(rad)
            front_y = self.y - self.radius * math.cos(rad)
            mine_vx = self.vx + 50 * math.sin(rad)
            mine_vy = self.vy - 50 * math.cos(rad)
            mine = Mine(front_x, front_y, mine_vx, mine_vy, enemy, game_time, launching=True)
            self.deployed_mines.append(mine)
            if len(self.deployed_mines) > 8:
                self.deployed_mines.pop(0)
            return mine
        return None

    def fire_plasmoid_ring(self, game_time):
        if self.special_timer > 0 or self.energy < self.special_energy_cost:
            return []
        self.energy -= self.special_energy_cost
        if self.energy == self.max_energy:
            self.special_timer = self.special_wait / 2
        else:
            self.special_timer = self.special_wait
        plasmoids = []
        for i in range(16):
            angle_deg = i * 22.5
            rad = math.radians(angle_deg)
            front_x = self.x + self.radius * math.sin(rad)
            front_y = self.y - self.radius * math.cos(rad)
            vx = 50 * math.sin(rad)
            vy = -50 * math.cos(rad)
            plasmoid = Plasmoid(front_x, front_y, vx, vy, game_time)
            plasmoids.append(plasmoid)
        return plasmoids

    def fire_laser_defense(self, targets, game_time):
        """
        Для ShipB, при нажатии RShift/Q, вместо лазерной защиты активируется плазмоидный режим.
        Метод вызывает fire_plasmoid_ring и возвращает список созданных плазмоидов.
        """

