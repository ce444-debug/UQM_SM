# project/ships/ship_b.py
import math
from project.ships.base_ship import BaseShip
from project.config import FIELD_W, FIELD_H
from project.utils import wrap_delta, wrap_position
from project.entities.mine import Mine, Plasmoid

class ShipB(BaseShip):
    def __init__(self, x, y, color):
        super().__init__(x, y, color)
        self.name = "KOHR-AH MARAUDER"
        self.max_crew = 42
        self.crew = 42
        self.max_energy = 42
        self.energy = 42
        self.energy_regeneration = 1
        self.energy_wait = 4 / 60.0
        self.energy_timer = self.energy_wait

        # Параметры минного пускателя (основное оружие)
        self.weapon_energy_cost = 6
        self.weapon_wait = 6 / 60.0
        self.weapon_timer = 0

        # Параметры плазмоидного кольца (спецоружие)
        self.special_energy_cost = 21
        self.special_wait = 9 / 60.0
        self.special_timer = 0

        self.max_thrust = 30.0
        self.thrust_increment = 3.0
        self.thrust_wait = 4 / 60.0
        self.turn_speed = 90.0

        # Управление минами
        self.deployed_mines = []  # Фиксированные мины
        self.current_mine = None  # Мина в режиме запуска

    def start_mine_launch(self, enemy, game_time):
        """
        Создает мину, которая при запуске летит по заданной траектории независимо от дальнейшего движения корабля.
        """
        if self.current_mine is None and self.weapon_timer <= 0 and self.energy >= self.weapon_energy_cost:
            self.energy -= self.weapon_energy_cost
            self.weapon_timer = self.weapon_wait
            rad = math.radians(self.angle)
            front_x = self.x + self.radius * math.sin(rad)
            front_y = self.y - self.radius * math.cos(rad)
            # Увеличенная скорость: используем множитель 150 вместо 50
            mine_vx = self.vx + 150 * math.sin(rad)
            mine_vy = self.vy - 150 * math.cos(rad)
            mine = Mine(front_x, front_y, mine_vx, mine_vy, enemy, game_time, launching=True)
            self.current_mine = mine
            return mine
        return None

    def release_mine(self):
        """
        Фиксирует мину, устанавливая её скорость равной нулю, и добавляет её в список размещённых мин.
        Если число размещённых мин превышает 8, удаляется самая старая.
        """
        if self.current_mine:
            self.current_mine.vx = 0
            self.current_mine.vy = 0
            self.current_mine.launching = False
            self.deployed_mines.append(self.current_mine)
            if len(self.deployed_mines) > 8:
                oldest = self.deployed_mines.pop(0)
                oldest.active = False
            released = self.current_mine
            self.current_mine = None
            return released
        return None

    def fire_missile(self, enemy, game_time):
        raise NotImplementedError("ShipB uses mines as its primary weapon.")

    def fire_laser_defense(self, targets, game_time):
        """
        Создает плазмоидное кольцо из 16 плазмоидов, равномерно распределенных по кругу.
        Все элементы кольца имеют одинаковое время запуска (ring_start_time) и следуют за кораблем.
        """
        if self.special_timer > 0 or self.energy < self.special_energy_cost:
            return []
        self.energy -= self.special_energy_cost
        self.special_timer = self.special_wait
        ring_start_time = game_time
        plasmoids = []
        for i in range(16):
            angle_deg = i * 22.5
            rad = math.radians(angle_deg)
            p = Plasmoid(rad, ring_start_time, orbit_speed=50.0, lifetime=1.0)
            p.owner = self
            plasmoids.append(p)
        return plasmoids

    def update(self, dt):
        super().update(dt)
        if self.current_mine and not self.current_mine.active:
            self.current_mine = None
