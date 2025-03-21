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

        # Флаг гравитационного манёвра (разрешает превышение max_thrust)
        self.in_gravity_field = False

        # Новый флаг жизни – корабль считается живым, если alive == True
        self.alive = True

    def update(self, dt):
        # Обновляем положение
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)

        if self.spawn_timer > 0:
            self.spawn_timer = max(0, self.spawn_timer - dt)

        # Обновляем энергию
        self.energy_timer -= dt
        if self.energy_timer <= 0:
            if self.energy < self.max_energy:
                self.energy = min(self.max_energy, self.energy + self.energy_regeneration)
            self.energy_timer = self.energy_wait

        # Обновляем таймеры оружия
        if self.weapon_timer > 0:
            self.weapon_timer -= dt
        if self.special_timer > 0:
            self.special_timer -= dt

        # Обновляем лазерные лучи
        new_lasers = []
        for (tx, ty, t) in self.active_lasers:
            t -= dt
            if t > 0:
                new_lasers.append((tx, ty, t))
        self.active_lasers = new_lasers

        # Плавное выравнивание вектора скорости к направлению корабля
        current_speed = math.hypot(self.vx, self.vy)
        if current_speed > 0:
            current_velocity_angle = math.degrees(math.atan2(self.vx, -self.vy))
            angle_diff = (self.angle - current_velocity_angle + 180) % 360 - 180
            allowed_rotation = dt * self.turn_speed * 10.0 / max(current_speed, 1)
            rotation = math.copysign(min(abs(angle_diff), allowed_rotation), angle_diff)
            new_velocity_angle = current_velocity_angle + rotation
            new_rad = math.radians(new_velocity_angle)
            self.vx = current_speed * math.sin(new_rad)
            self.vy = -current_speed * math.cos(new_rad)

    def take_damage(self, amount):
        if not self.alive:
            return
        self.crew -= amount
        if self.crew <= 0:
            self.alive = False
            print(f"{self.name} (ID {self.id}) destroyed!")

    @property
    def active(self):
        return self.alive

    # Унифицированные методы вооружения – должны быть переопределены в подклассах
    def fire_primary(self, enemy, game_time):
        raise NotImplementedError("fire_primary() must be implemented by subclass.")

    def fire_secondary(self, targets, game_time):
        raise NotImplementedError("fire_secondary() must be implemented by subclass.")

    def accelerate(self):
        """Применяет ускорение в направлении, на которое направлен корабль.
        Если текущая скорость превышает max_thrust и корабль не находится в гравитационном поле,
        ускорение не применяется."""
        current_speed = math.hypot(self.vx, self.vy)
        if current_speed > self.max_thrust and not self.in_gravity_field:
            return  # Не ускоряем, если скорость уже превышена.
        rad = math.radians(self.angle)
        self.vx += self.thrust_increment * math.sin(rad)
        self.vy += self.thrust_increment * math.sin(rad)
