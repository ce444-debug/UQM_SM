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

        # Оружейные параметры минного пускателя
        self.weapon_energy_cost = 6
        self.weapon_wait = 6 / 60.0
        self.weapon_timer = 0

        # Оружейные параметры плазмоидного кольца
        self.special_energy_cost = 21
        self.special_wait = 9 / 60.0
        self.special_timer = 0

        self.max_thrust = 30.0
        self.thrust_increment = 3.0
        self.thrust_wait = 4 / 60.0
        self.turn_speed = 90.0

        # Списки мин
        self.deployed_mines = []
        self.current_mine = None

    def start_mine_launch(self, enemy, game_time):
        if self.current_mine is None and self.weapon_timer <= 0 and self.energy >= self.weapon_energy_cost:
            rad = math.radians(self.angle)
            front_x = self.x + self.radius * math.sin(rad)
            front_y = self.y - self.radius * math.cos(rad)
            mine_vx = self.vx + 50 * math.sin(rad)
            mine_vy = self.vy - 50 * math.cos(rad)
            self.current_mine = Mine(front_x, front_y, mine_vx, mine_vy, enemy, game_time, launching=True)
            self.energy -= self.weapon_energy_cost
            if self.energy == self.max_energy:
                self.weapon_timer = self.weapon_wait / 2
            else:
                self.weapon_timer = self.weapon_wait
            return self.current_mine
        return None

    def release_mine(self):
        if self.current_mine:
            self.current_mine.launching = False
            self.deployed_mines.append(self.current_mine)
            if len(self.deployed_mines) > 8:
                self.deployed_mines.pop(0)
            released = self.current_mine
            self.current_mine = None
            return released
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
            plasmoid.owner = self  # Устанавливаем владельца
            plasmoids.append(plasmoid)
        return plasmoids

    def fire_laser_defense(self, game_time):
        return self.fire_plasmoid_ring(game_time)
