import math
import random


class AIController:
    def __init__(self, ship, difficulty="Medium"):
        """
        Базовый AI-контроллер с общими методами навигации, уклонения и стрельбы.
        difficulty: "Easy", "Medium" или "Hard"
        """
        self.ship = ship
        self.difficulty = difficulty
        if self.difficulty == "Easy":
            self.reaction_time = 0.5  # замедленная реакция
            self.dodge_chance = 0.3  # 30% вероятность уклонения
        elif self.difficulty == "Medium":
            self.reaction_time = 0.3
            self.dodge_chance = 0.6
        else:  # Hard
            self.reaction_time = 0.1
            self.dodge_chance = 1.0
        self._decision_timer = 0.0

    def update(self, dt, enemy, obstacles, projectiles):
        # Отладка: выводим информацию об update
        # print(f"[AI UPDATE] Ship: {self.ship.name} | dt: {dt:.3f} | reaction_time: {self.reaction_time}")
        self._decision_timer += dt
        if self._decision_timer < self.reaction_time:
            return  # пропускаем обновление, если не прошёл интервал реакции
        self._decision_timer = 0.0

        # Проверяем препятствия – если обнаружено, получаем угол уклонения
        avoid_direction = self.avoid_obstacles(obstacles)
        #if avoid_direction is not None:
            # print(f"[AI] {self.ship.name} обнаружил препятствие, корректировка угла на {avoid_direction:.1f}")

        # Получаем базовый целевой угол и решение о тяге – определяется в подклассах
        target_angle, thrust = self.determine_movement(enemy)
        #print(f"[AI] {self.ship.name} базовый target_angle: {target_angle:.1f}, thrust: {thrust}")

        # Если обнаружено препятствие, переопределяем целевой угол
        if avoid_direction is not None:
            target_angle = avoid_direction
            thrust = True

        # Если обнаружены вражеские снаряды, по вероятности (зависит от сложности) уклоняемся
        if self.check_dodge_needed(projectiles):
            dodge_angle = (self.ship.angle + (90 if random.random() < 0.5 else -90)) % 360
            #print(f"[AI] {self.ship.name} уклоняется: новый target_angle {dodge_angle:.1f}")
            target_angle = dodge_angle
            thrust = True

        # Поворачиваем корабль к целевому углу
        self.turn_towards(target_angle, dt)
        # Если требуется – включаем ускорение
        if thrust:
            #print(f"[AI] {self.ship.name} применяет ускорение")
            self.ship.accelerate()
        # Вызываем метод стрельбы (определяется в подклассах)
        self.fire_weapons(enemy)

    def determine_movement(self, enemy):
        raise NotImplementedError("determine_movement() must be implemented in subclass.")

    def fire_weapons(self, enemy):
        raise NotImplementedError("fire_weapons() must be implemented in subclass.")

    def avoid_obstacles(self, obstacles):
        for obs in obstacles:
            dx = obs.x - self.ship.x
            dy = obs.y - self.ship.y
            safe_dist = (obs.radius + getattr(self.ship, "radius", 0) + 50) ** 2
            if dx * dx + dy * dy < safe_dist:
                angle_to_obs = math.degrees(math.atan2(dy, dx))
                avoid_angle = (angle_to_obs + 90) % 360
                return avoid_angle
        return None

    def check_dodge_needed(self, projectiles):
        for proj in projectiles:
            dx = self.ship.x - proj.x
            dy = self.ship.y - proj.y
            if dx * dx + dy * dy < 100 ** 2:
                proj_angle = math.degrees(math.atan2(proj.vy, proj.vx))
                angle_to_ship = math.degrees(math.atan2(dy, dx))
                angle_diff = abs((proj_angle - angle_to_ship + 180) % 360 - 180)
                if angle_diff < 30:
                    if random.random() < self.dodge_chance:
                        return True
        return False

    def turn_towards(self, target_angle, dt):
        turn_rate = getattr(self.ship, "turn_speed", 180)
        diff = ((target_angle - self.ship.angle + 180) % 360) - 180
        if abs(diff) < turn_rate * dt:
            self.ship.angle = target_angle
        else:
            self.ship.angle += math.copysign(turn_rate * dt, diff)
            self.ship.angle %= 360


class EarthlingAIController(AIController):
    def determine_movement(self, enemy):
        dx = enemy.x - self.ship.x
        dy = enemy.y - self.ship.y
        angle_to_enemy = math.degrees(math.atan2(dy, dx))
        # Агрессивно – всегда двигаться в сторону врага
        return angle_to_enemy, True

    def fire_weapons(self, enemy):
        dx = enemy.x - self.ship.x
        dy = enemy.y - self.ship.y
        angle_to_enemy = math.degrees(math.atan2(dy, dx))
        angle_diff = abs((angle_to_enemy - self.ship.angle + 180) % 360 - 180)
        missile_range = 700.0
        distance = math.hypot(dx, dy)
        if angle_diff < 30 and distance <= missile_range:
            #print(f"[AI] {self.ship.name} стреляет ракетой (fire_primary)")
            self.ship.fire_primary(enemy, 0)


class KohrAhAIController(AIController):
    def __init__(self, ship, difficulty="Medium"):
        super().__init__(ship, difficulty)
        self.mine_cooldown = 0.0

    def determine_movement(self, enemy):
        # Агрессивная тактика: всегда поворачиваемся к врагу и сближаемся
        dx = enemy.x - self.ship.x
        dy = enemy.y - self.ship.y
        target_angle = math.degrees(math.atan2(dy, dx))
        return target_angle, True

    def fire_weapons(self, enemy):
        # Всегда запускаем мины как основное оружие
        #print(f"[AI] {self.ship.name} запускает мины (fire_primary)")
        self.ship.fire_primary(enemy, 0)
        # Если враг близко, используем вторичное оружие (плазмоиды)
        dx = enemy.x - self.ship.x
        dy = enemy.y - self.ship.y
        distance = math.hypot(dx, dy)
        if distance < 300:
            if self.mine_cooldown <= 0:
                #print(f"[AI] {self.ship.name} использует плазмоиды (fire_secondary)")
                self.ship.fire_secondary([enemy], 0)
                if self.difficulty == "Hard":
                    self.mine_cooldown = 0.8
                elif self.difficulty == "Medium":
                    self.mine_cooldown = 1.0
                else:
                    self.mine_cooldown = 1.5
        if self.mine_cooldown > 0:
            self.mine_cooldown -= self.reaction_time
