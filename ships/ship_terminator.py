import math
from project.ships.base_ship import BaseShip


class ShipTerminator(BaseShip):
    def __init__(self, x, y, color):
        super().__init__(x, y, color)
        self.name = "YEHAT TERMINATOR"
        self.max_crew = 20
        self.crew = 20
        self.max_energy = 10
        self.energy = 10
        self.energy_regeneration = 2
        self.energy_wait = 6 / 60.0
        self.energy_timer = self.energy_wait

        self.weapon_energy_cost = 1
        self.weapon_wait = 0 / 60.0
        self.weapon_timer = 0

        self.special_energy_cost = 3
        self.special_wait = 2 / 60.0
        self.special_timer = 0

        self.max_thrust = 30.0
        self.thrust_increment = 6.0
        self.thrust_wait = 2 / 60.0
        self.turn_speed = 90.0

        self.shield_timer = 0

        self.cost = self.max_crew  # Стоимость корабля

    def fire_primary(self, enemy, game_time):
        if self.weapon_timer <= 0 and self.energy >= self.weapon_energy_cost:
            self.energy -= self.weapon_energy_cost
            self.weapon_timer = self.weapon_wait
            rad = math.radians(self.angle)
            forward_x = math.sin(rad)
            forward_y = -math.cos(rad)
            right_x = math.cos(rad)
            right_y = math.sin(rad)
            front_offset = self.radius
            wing_offset = self.radius
            left_x = self.x + forward_x * front_offset - right_x * wing_offset
            left_y = self.y + forward_y * front_offset - right_y * wing_offset
            right_tip_x = self.x + forward_x * front_offset + right_x * wing_offset
            right_tip_y = self.y + forward_y * front_offset + right_y * wing_offset
            missile_speed = 50.0
            missile_vx = self.vx + forward_x * missile_speed
            missile_vy = self.vy + forward_y * missile_speed
            from project.entities.missile import Missile
            missile_left = Missile(left_x, left_y, missile_vx, missile_vy, None, game_time)
            missile_left.damage = 1
            missile_left.owner = self
            missile_right = Missile(right_tip_x, right_tip_y, missile_vx, missile_vy, None, game_time)
            missile_right.damage = 1
            missile_right.owner = self
            return [missile_left, missile_right]
        return []

    def fire_secondary(self, targets, game_time):
        if self.special_timer <= 0 and self.energy >= self.special_energy_cost:
            self.energy -= self.special_energy_cost
            self.special_timer = self.special_wait
            self.shield_timer = 0.5
        return []

    def update(self, dt):
        super().update(dt)
        if self.shield_timer > 0:
            self.shield_timer -= dt

    def take_damage(self, amount):
        if self.shield_timer > 0:
            return
        super().take_damage(amount)
