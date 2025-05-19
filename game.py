import pygame
import sys
import math

from project.config import *
from project.model.utils import spawn_ship, wrap_delta, world_to_screen
from project.model.gravity import apply_gravity
from project.entities.planet import Planet
from project.entities.asteroid import Asteroid
from project.entities.camera import Camera
from project.ships.registry import SHIP_CLASSES
from project.entities.mine import Plasmoid
from project.model.collisions import (
    handle_planet_collision,
    handle_ship_asteroid_collision,
    handle_ship_ship_collision,
    handle_asteroid_collision,
)
from menu import PauseMenu


class Game:
    def __init__(self, config, menu):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Combat Zone with Gravity-Boosted Ships")
        self.clock = pygame.time.Clock()

        self.config = config
        self.menu = menu
        self.game_mode = config["mode"]

        self.team1_fleet = [
            SHIP_CLASSES[ship]
            for ship in config["teams"]["Team 1"]
            if ship is not None
        ]
        self.team2_fleet = [
            SHIP_CLASSES[ship]
            for ship in config["teams"]["Team 2"]
            if ship is not None
        ]

        if not self.team1_fleet or not self.team2_fleet:
            print("Error: One of the fleets is empty!")
            self.menu.save_last_config()
            pygame.quit()
            sys.exit()

        # Храним индексы доступных ячеек вместо классов кораблей
        self.team1_remaining = [i for i in range(len(config["teams"]["Team 1"])) if config["teams"]["Team 1"][i] is not None]
        self.team2_remaining = [i for i in range(len(config["teams"]["Team 2"])) if config["teams"]["Team 2"][i] is not None]

        # Отладка
        print(f"Config mode: {self.game_mode}")
        print(f"Team 1 settings: {config['settings']['Team 1']}")
        print(f"Team 2 settings: {config['settings']['Team 2']}")
        print(f"Team 1 config: {config['teams']['Team 1']}")
        print(f"Team 2 config: {config['teams']['Team 2']}")
        print(f"Team 1 fleet: {[c.__name__ for c in self.team1_fleet]}")
        print(f"Team 2 fleet: {[c.__name__ for c in self.team2_fleet]}")

        # Initial ship selection from menu
        ship1_name = config['initial_ships']['Team 1']
        if ship1_name == '?':
            if self.team1_remaining:
                selected_idx = self.team1_remaining.pop(0)
                selected_ship = SHIP_CLASSES[config['teams']['Team 1'][selected_idx]]
            else:
                selected_ship = self.team1_fleet[0]
        else:
            selected_idx = None
            for idx in self.team1_remaining:
                if config['teams']['Team 1'][idx] == ship1_name:
                    selected_idx = idx
                    break
            if selected_idx is not None:
                selected_ship = SHIP_CLASSES[ship1_name]
                self.team1_remaining.remove(selected_idx)
            else:
                selected_idx = self.team1_remaining.pop(0) if self.team1_remaining else 0
                selected_ship = SHIP_CLASSES[config['teams']['Team 1'][selected_idx]]
        sx1, sy1 = spawn_ship()
        self.ship1 = selected_ship(sx1, sy1, (255, 100, 100))

        ship2_name = config['initial_ships']['Team 2']
        if ship2_name == '?':
            if self.team2_remaining:
                selected_idx = self.team2_remaining.pop(0)
                selected_ship = SHIP_CLASSES[config['teams']['Team 2'][selected_idx]]
            else:
                selected_ship = self.team2_fleet[0]
        else:
            selected_idx = None
            for idx in self.team2_remaining:
                if config['teams']['Team 2'][idx] == ship2_name:
                    selected_idx = idx
                    break
            if selected_idx is not None:
                selected_ship = SHIP_CLASSES[ship2_name]
                self.team2_remaining.remove(selected_idx)
            else:
                selected_idx = self.team2_remaining.pop(0) if self.team2_remaining else 0
                selected_ship = SHIP_CLASSES[config['teams']['Team 2'][selected_idx]]
        sx2, sy2 = spawn_ship()
        self.ship2 = selected_ship(sx2, sy2, (100, 200, 255))

        # AI для Cyborg
        if not self.game_mode.startswith("Human vs Human"):
            from project.ai_controller import EarthlingAIController
            self.ship1.ai_controller = (
                EarthlingAIController(self.ship1, difficulty=self.cyborg_difficulty("Team 1"))
                if self.is_cyborg("Team 1")
                else None
            )
            self.ship2.ai_controller = (
                EarthlingAIController(self.ship2, difficulty=self.cyborg_difficulty("Team 2"))
                if self.is_cyborg("Team 2")
                else None
            )
        else:
            self.ship1.ai_controller = None
            self.ship2.ai_controller = None

        # Планета и камера
        self.planet = Planet(FIELD_W / 2, FIELD_H / 2, 30, (180, 180, 180))
        self.cam = Camera(FIELD_W / 2, FIELD_H / 2)
        self.globalCamX = self.cam.x
        self.globalCamY = self.cam.y
        self.prevCamX = self.cam.x
        self.prevCamY = self.cam.y

        # Звезды
        from project.stars import generate_colored_stars
        self.star_layer_far = generate_colored_stars(180)
        self.star_layer_mid = generate_colored_stars(120)
        self.star_layer_near = generate_colored_stars(80)

        # Астероиды
        self.asteroids = []
        for _ in range(5):
            x = random.uniform(0, FIELD_W)
            y = random.uniform(0, FIELD_H)
            radius = random.randint(8, 12)
            vx = random.uniform(-50, 50)
            vy = random.uniform(-50, 50)
            color = (200, 200, 200)
            self.asteroids.append(Asteroid(x, y, radius, vx, vy, color))

        self.missiles = []
        self.game_time = 0
        self.running = True
        self.dt = 0

    def wait_for_key(self, message):
        font = pygame.font.SysFont("Arial", 36)
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.menu.save_last_config()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    waiting = False
            self.screen.fill((0, 0, 0))
            text = font.render(message, True, (255, 255, 255))
            self.screen.blit(
                text,
                (
                    SCREEN_W // 2 - text.get_width() // 2,
                    SCREEN_H // 2 - text.get_height() // 2,
                ),
            )
            pygame.display.flip()
            self.clock.tick(30)

    def is_human(self, team: str) -> bool:
        return "human" in self.config["settings"][team]["control"].lower()

    def is_cyborg(self, team: str) -> bool:
        return "cyborg" in self.config["settings"][team]["control"].lower()

    def cyborg_difficulty(self, team: str) -> str:
        ctrl = self.config["settings"][team]["control"].lower()
        if "weak" in ctrl:
            return "Easy"
        if "awesome" in ctrl:
            return "Hard"
        return "Medium"

    def pause(self):
        pause_menu = PauseMenu(self.screen, self.clock)
        pause_menu.set_super_menu(self.menu)
        return pause_menu.display()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.menu.save_last_config()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    option = self.pause()
                    if option == "RESUME":
                        pass
                    elif option == "MENU":
                        self.menu.save_last_config()
                        self.running = False
                        return "MENU"
                    elif option == "QUIT":
                        self.menu.save_last_config()
                        pygame.quit()
                        sys.exit()
                if not (
                        hasattr(self.ship1, "ai_controller")
                        and self.ship1.ai_controller is not None
                ):
                    if event.key == pygame.K_a:
                        primary = self.ship1.fire_primary(self.ship2, self.game_time)
                        if primary:
                            if isinstance(primary, list):
                                self.missiles.extend(primary)
                            else:
                                self.missiles.append(primary)
                    if event.key == pygame.K_q:
                        special = self.ship1.fire_secondary(
                            [self.ship2] + self.asteroids + self.missiles, self.game_time
                        )
                        if special:
                            if isinstance(special, list):
                                self.missiles.extend(special)
                            else:
                                self.missiles.append(special)
                if not (
                        hasattr(self.ship2, "ai_controller")
                        and self.ship2.ai_controller is not None
                ):
                    if event.key == pygame.K_RCTRL:
                        primary = self.ship2.fire_primary(self.ship1, self.game_time)
                        if primary:
                            if isinstance(primary, list):
                                self.missiles.extend(primary)
                            else:
                                self.missiles.append(primary)
                    if event.key == pygame.K_RSHIFT:
                        special = self.ship2.fire_secondary(
                            [self.ship1] + self.asteroids + self.missiles, self.game_time
                        )
                        if special:
                            if isinstance(special, list):
                                self.missiles.extend(special)
                            else:
                                self.missiles.append(special)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    if hasattr(self.ship1, "release_mine"):
                        mine = self.ship1.release_mine()
                        if mine and mine not in self.missiles:
                            self.missiles.append(mine)
                if event.key == pygame.K_RCTRL:
                    if hasattr(self.ship2, "release_mine"):
                        mine = self.ship2.release_mine()
                        if mine and mine not in self.missiles:
                            self.missiles.append(mine)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            if hasattr(self.ship1, "current_mine") and self.ship1.current_mine is not None:
                if self.ship1.current_mine not in self.missiles:
                    self.missiles.append(self.ship1.current_mine)
        if keys[pygame.K_RCTRL]:
            if hasattr(self.ship2, "current_mine") and self.ship2.current_mine is not None:
                if self.ship2.current_mine not in self.missiles:
                    self.missiles.append(self.ship2.current_mine)

        if (
                not hasattr(self.ship1, "ai_controller")
                or self.ship1.ai_controller is None
        ):
            if keys[pygame.K_s]:
                self.ship1.angle = (self.ship1.angle - self.ship1.turn_speed * self.dt) % 360
            if keys[pygame.K_f]:
                self.ship1.angle = (self.ship1.angle + self.ship1.turn_speed * self.dt) % 360
            if keys[pygame.K_e]:
                if not hasattr(self.ship1, "thrust_timer"):
                    self.ship1.thrust_timer = 0
                self.ship1.thrust_timer += self.dt
                while self.ship1.thrust_timer >= self.ship1.thrust_wait:
                    rad = math.radians(self.ship1.angle)
                    thrust_dx = math.sin(rad)
                    thrust_dy = -math.cos(rad)
                    speed = math.hypot(self.ship1.vx, self.ship1.vy)
                    if (
                            speed > self.ship1.max_thrust
                            and speed > 0
                            and (self.ship1.vx * thrust_dx + self.ship1.vy * thrust_dy) / speed > 0
                            and not self.ship1.in_gravity_field
                    ):
                        self.ship1.thrust_timer -= self.ship1.thrust_wait
                        continue
                    if (self.ship1.vx * thrust_dx + self.ship1.vy * thrust_dy) / max(speed, 1) < 0:
                        braking_multiplier = 2.0
                        self.ship1.vx += braking_multiplier * self.ship1.thrust_increment * thrust_dx
                        self.ship1.vy += braking_multiplier * self.ship1.thrust_increment * thrust_dy
                    else:
                        self.ship1.vx += self.ship1.thrust_increment * thrust_dx
                        self.ship1.vy += self.ship1.thrust_increment * thrust_dy
                    self.ship1.thrust_timer -= self.ship1.thrust_wait

        if (
                not hasattr(self.ship2, "ai_controller")
                or self.ship2.ai_controller is None
        ):
            if keys[pygame.K_LEFT]:
                self.ship2.angle = (self.ship2.angle - self.ship2.turn_speed * self.dt) % 360
            if keys[pygame.K_RIGHT]:
                self.ship2.angle = (self.ship2.angle + self.ship2.turn_speed * self.dt) % 360
            if keys[pygame.K_UP]:
                if not hasattr(self.ship2, "thrust_timer"):
                    self.ship2.thrust_timer = 0
                self.ship2.thrust_timer += self.dt
                while self.ship2.thrust_timer >= self.ship2.thrust_wait:
                    rad = math.radians(self.ship2.angle)
                    thrust_dx = math.sin(rad)
                    thrust_dy = -math.cos(rad)
                    speed = math.hypot(self.ship2.vx, self.ship2.vy)
                    if (
                            speed > self.ship2.max_thrust
                            and speed > 0
                            and (self.ship2.vx * thrust_dx + self.ship2.vy * thrust_dy) / speed > 0
                            and not self.ship2.in_gravity_field
                    ):
                        self.ship2.thrust_timer -= self.ship2.thrust_wait
                        continue
                    if (self.ship1.vx * thrust_dx + self.ship1.vy * thrust_dy) / max(speed, 1) < 0:
                        braking_multiplier = 2.0
                        self.ship2.vx += braking_multiplier * self.ship2.thrust_increment * thrust_dx
                        self.ship2.vy += braking_multiplier * self.ship2.thrust_increment * thrust_dy
                    else:
                        self.ship2.vx += self.ship2.thrust_increment * thrust_dx
                        self.ship2.vy += self.ship2.thrust_increment * thrust_dy
                    self.ship2.thrust_timer -= self.ship2.thrust_wait

    def update(self, dt):
        self.dt = dt
        self.game_time += dt

        self.ship1.in_gravity_field = False
        self.ship2.in_gravity_field = False

        if hasattr(self.ship1, "ai_controller") and self.ship1.ai_controller is not None:
            self.ship1.ai_controller.update(dt, self.ship2, self.asteroids + [self.planet], self.missiles)
        if hasattr(self.ship2, "ai_controller") and self.ship2.ai_controller is not None:
            self.ship2.ai_controller.update(dt, self.ship1, self.asteroids + [self.planet], self.missiles)

        apply_gravity(self.ship1, self.planet, dt)
        apply_gravity(self.ship2, self.planet, dt)
        for projectile in self.missiles:
            if hasattr(projectile, "launching") and projectile.launching:
                apply_gravity(projectile, self.planet, dt)

        self.ship1.update(dt)
        self.ship2.update(dt)
        for asteroid in self.asteroids:
            asteroid.update(dt)
        for projectile in self.missiles:
            if isinstance(projectile, Plasmoid):
                projectile.update(dt, self.game_time)
            else:
                projectile.update(dt)

        for projectile in self.missiles:
            if not projectile.active:
                continue
            if hasattr(projectile, "target") and projectile.target is not None:
                tx = projectile.target.x
                ty = projectile.target.y
                d_x = wrap_delta(projectile.x, tx, FIELD_W)
                d_y = wrap_delta(projectile.y, ty, FIELD_H)
                target_radius = getattr(projectile.target, "radius", 0)
                if math.hypot(d_x, d_y) < (projectile.radius + target_radius):
                    projectile.target.take_damage(projectile.damage)
                    projectile.active = False
                    continue
            elif hasattr(projectile, "owner") and projectile.owner is not None:
                if projectile.owner.id == self.ship1.id:
                    enemy = self.ship2
                else:
                    enemy = self.ship1
                d_x = wrap_delta(projectile.x, enemy.x, FIELD_W)
                d_y = wrap_delta(projectile.y, enemy.y, FIELD_H)
                if math.hypot(d_x, d_y) < (projectile.radius + enemy.radius):
                    enemy.take_damage(projectile.damage)
                    projectile.active = False
                    continue
            if isinstance(projectile, Plasmoid) and projectile.active:
                for other_proj in self.missiles:
                    if other_proj is projectile or not other_proj.active:
                        continue
                    if hasattr(other_proj, "owner") and other_proj.owner is not None:
                        if other_proj.owner.id != projectile.owner.id:
                            dx = wrap_delta(projectile.x, other_proj.x, FIELD_W)
                            dy = wrap_delta(projectile.y, other_proj.y, FIELD_H)
                            if math.hypot(dx, dy) < (projectile.radius + other_proj.radius):
                                projectile.active = False
                                other_proj.active = False
                                break
                if not projectile.active:
                    continue
            for asteroid in self.asteroids:
                if (
                        abs(projectile.x - asteroid.x) > (projectile.radius + asteroid.radius)
                        or abs(projectile.y - asteroid.y) > (projectile.radius + asteroid.radius)
                ):
                    continue
                dx = wrap_delta(projectile.x, asteroid.x, FIELD_W)
                dy = wrap_delta(projectile.y, asteroid.y, FIELD_H)
                if math.hypot(dx, dy) < (projectile.radius + asteroid.radius):
                    asteroid.active = False
                    projectile.active = False
                    break
            dx = wrap_delta(projectile.x, self.planet.x, FIELD_W)
            dy = wrap_delta(projectile.y, self.planet.y, FIELD_H)
            if math.hypot(dx, dy) < (projectile.radius + self.planet.radius):
                projectile.active = False

        for i in range(len(self.missiles)):
            for j in range(i + 1, len(self.missiles)):
                proj1 = self.missiles[i]
                proj2 = self.missiles[j]
                if not proj1.active or not proj2.active:
                    continue
                if hasattr(proj1, "owner") and hasattr(proj2, "owner") and proj1.owner.id != proj2.owner.id:
                    dx = wrap_delta(proj1.x, proj2.x, FIELD_W)
                    dy = wrap_delta(proj1.y, proj2.y, FIELD_H)
                    if math.hypot(dx, dy) <= (proj1.radius + proj2.radius):
                        proj1.active = False
                        proj2.active = False

        self.missiles = [m for m in self.missiles if m.active]
        self.asteroids = [a for a in self.asteroids if a.active]

        handle_planet_collision(self.ship1, self.planet, self.game_time)
        handle_planet_collision(self.ship2, self.planet, self.game_time)
        for asteroid in self.asteroids:
            handle_ship_asteroid_collision(self.ship1, asteroid)
            handle_ship_asteroid_collision(self.ship2, asteroid)
        handle_ship_ship_collision(self.ship1, self.ship2)
        for i in range(len(self.asteroids)):
            for j in range(i + 1, len(self.asteroids)):
                handle_asteroid_collision(self.asteroids[i], self.asteroids[j])
        for i, asteroid in enumerate(self.asteroids):
            dx = wrap_delta(asteroid.x, self.planet.x, FIELD_W)
            dy = wrap_delta(asteroid.y, self.planet.y, FIELD_H)
            if math.hypot(dx, dy) < (self.planet.radius + asteroid.radius):
                self.asteroids[i] = self.generate_offscreen_asteroid(self.cam, 1.0)

        self.cam.update_center_on_two_ships(self.ship1, self.ship2)
        dx_cam = self.cam.x - self.prevCamX
        dy_cam = self.cam.y - self.prevCamY
        if dx_cam > FIELD_W / 2:
            dx_cam -= FIELD_W
        elif dx_cam < -FIELD_W / 2:
            dx_cam += FIELD_W
        if dy_cam > FIELD_H / 2:
            dy_cam -= FIELD_H
        elif dy_cam < -FIELD_H / 2:
            dy_cam += FIELD_H
        self.globalCamX += dx_cam
        self.globalCamY += dy_cam
        self.prevCamX = self.cam.x
        self.prevCamY = self.cam.y

        self.check_ship_replacement()

    def generate_offscreen_asteroid(self, cam, zoom):
        margin = 20
        while True:
            x = random.uniform(0, FIELD_W)
            y = random.uniform(0, FIELD_H)
            sx, sy = world_to_screen(x, y, cam.x, cam.y, zoom)
            if (
                    sx < -margin
                    or sx > GAME_SCREEN_W + margin
                    or sy < -margin
                    or sy > SCREEN_H + margin
            ):
                break
        radius = random.randint(8, 12)
        vx = random.uniform(-50, 50)
        vy = random.uniform(-50, 50)
        color = (200, 200, 200)
        new_ast = Asteroid(x, y, radius, vx, vy, color)
        from project.config import ASTEROID_ROTATION_AXIS
        new_ast.angular_velocity = ASTEROID_ROTATION_AXIS * random.uniform(50, 180)
        return new_ast

    def check_ship_replacement(self):
        need1 = getattr(self.ship1, "dead", False)
        need2 = getattr(self.ship2, "dead", False)
        if not (need1 or need2):
            return

        print(f"Before replacement: team1_remaining={self.team1_remaining}")
        print(f"Before replacement: team2_remaining={self.team2_remaining}")

        if need1 and not self.team1_remaining:
            self.end_game("Team 2")
            return
        if need2 and not self.team2_remaining:
            self.end_game("Team 1")
            return

        new1, new2 = self.replacement_phase(need1, need2)

        from project.ai_controller import EarthlingAIController
        if need1:
            if new1 is None:
                self.end_game("Team 2")
                return
            sx1, sy1 = spawn_ship()
            self.ship1 = new1(sx1, sy1, (255, 100, 100))
            if self.config["settings"]["Team 1"]["control"].endswith("Cyborg"):
                diff1 = self.config["settings"]["Team 1"]["cyborg_difficulty"]
                self.ship1.ai_controller = EarthlingAIController(self.ship1, difficulty=diff1)
            else:
                self.ship1.ai_controller = None
            # Удаляем использованную ячейку
            if hasattr(self, "last_selected_idx1"):
                self.team1_remaining.remove(self.last_selected_idx1)
                delattr(self, "last_selected_idx1")

        if need2:
            if new2 is None:
                self.end_game("Team 1")
                return
            sx2, sy2 = spawn_ship()
            self.ship2 = new2(sx2, sy2, (100, 200, 255))
            if self.config["settings"]["Team 2"]["control"].endswith("Cyborg"):
                diff2 = self.config["settings"]["Team 2"]["cyborg_difficulty"]
                self.ship2.ai_controller = EarthlingAIController(self.ship2, difficulty=diff2)
            else:
                self.ship2.ai_controller = None
            # Удаляем использованную ячейку
            if hasattr(self, "last_selected_idx2"):
                self.team2_remaining.remove(self.last_selected_idx2)
                delattr(self, "last_selected_idx2")

    def replacement_phase(self, need_team1, need_team2):
        from project.ships.registry import SHIP_CLASSES
        names1 = list(self.config["teams"]["Team 1"])
        names2 = list(self.config["teams"]["Team 2"])
        team_slots = len(names1)

        print(f"names1: {names1}")
        print(f"names2: {names2}")
        print(f"team1_remaining: {self.team1_remaining}")
        print(f"team2_remaining: {self.team2_remaining}")
        print(f"SHIP_CLASSES keys: {list(SHIP_CLASSES.keys())}")

        # Проверяем доступность ячеек по индексам
        available1 = [i in self.team1_remaining for i in range(team_slots)]
        available2 = [i in self.team2_remaining for i in range(team_slots)]
        for i in range(team_slots):
            print(
                f"Team 1 slot {i} ({names1[i]}): available={available1[i]}")
            print(
                f"Team 2 slot {i} ({names2[i]}): available={available2[i]}")

        if not (need_team1 or need_team2):
            return None, None

        if need_team1 and need_team2 and not any(available1) and not any(available2):
            return None, None

        total = team_slots + 2
        cols = 4
        margin = 5
        cell_w = (GAME_SCREEN_W - 20 - (cols - 1) * margin) // cols
        cell_h = 40
        panel1 = pygame.Rect(10, 80, GAME_SCREEN_W - 20, (SCREEN_H - 100) // 2)
        panel2 = pygame.Rect(10, panel1.bottom + 20, GAME_SCREEN_W - 20, (SCREEN_H - 100) // 2)

        is_cyb1 = need_team1 and self.is_cyborg("Team 1")
        is_cyb2 = need_team2 and self.is_cyborg("Team 2")

        jump_delay = 400
        confirm_delay = 800
        start_t = pygame.time.get_ticks()

        idx1 = 0
        idx2 = 0
        jumped1 = jumped2 = False
        confirmed1 = not need_team1
        confirmed2 = not need_team2
        confirmed_idx1 = None
        confirmed_idx2 = None

        font = pygame.font.SysFont("Arial", 24)
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        GRAY = (200, 200, 200)
        YELLOW = (255, 255, 0)
        GREEN = (0, 255, 0)
        INACTIVE = (100, 100, 100)
        clock = pygame.time.Clock()

        while (need_team1 and not confirmed1) or (need_team2 and not confirmed2):
            now = pygame.time.get_ticks()
            elapsed = now - start_t

            if is_cyb1:
                if not jumped1 and elapsed >= jump_delay:
                    idx1 = team_slots
                    jumped1 = True
                if elapsed >= confirm_delay:
                    confirmed1 = True
                    confirmed_idx1 = idx1

            if is_cyb2:
                if not jumped2 and elapsed >= jump_delay:
                    idx2 = team_slots
                    jumped2 = True
                if elapsed >= confirm_delay:
                    confirmed2 = True
                    confirmed_idx2 = idx2

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.menu.save_last_config()
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if need_team1 and not is_cyb1 and not confirmed1:
                        if ev.key in (pygame.K_e, pygame.K_UP) and idx1 - cols >= 0:
                            idx1 -= cols
                        elif ev.key in (pygame.K_d, pygame.K_DOWN) and idx1 + cols < total:
                            idx1 += cols
                        elif ev.key in (pygame.K_s, pygame.K_LEFT) and idx1 > 0:
                            idx1 -= 1
                        elif ev.key in (pygame.K_f, pygame.K_RIGHT) and idx1 < total - 1:
                            idx1 += 1
                        elif ev.key in (pygame.K_a, pygame.K_RETURN):
                            is_available = idx1 >= team_slots or (idx1 < team_slots and available1[idx1])
                            print(
                                f"Team 1 confirm attempt: idx={idx1}, name={names1[idx1] if idx1 < team_slots else ('?' if idx1 == team_slots else 'X')}, available={is_available}")
                            if is_available:
                                confirmed1 = True
                                confirmed_idx1 = idx1
                    if need_team2 and not is_cyb2 and not confirmed2:
                        if ev.key == pygame.K_UP and idx2 - cols >= 0:
                            idx2 -= cols
                        elif ev.key == pygame.K_DOWN and idx2 + cols < total:
                            idx2 += cols
                        elif ev.key == pygame.K_LEFT and idx2 > 0:
                            idx2 -= 1
                        elif ev.key == pygame.K_RIGHT and idx2 < total - 1:
                            idx2 += 1
                        elif ev.key in (pygame.K_RCTRL, pygame.K_RETURN):
                            is_available = idx2 >= team_slots or (idx2 < team_slots and available2[idx2])
                            print(
                                f"Team 2 confirm attempt: idx={idx2}, name={names2[idx2] if idx2 < team_slots else ('?' if idx2 == team_slots else 'X')}, available={is_available}")
                            if is_available:
                                confirmed2 = True
                                confirmed_idx2 = idx2

            self.screen.fill(BLACK)

            def draw_panel(panel, names, available, idx, confirmed_idx, team_label):
                for i in range(total):
                    r, c = divmod(i, cols)
                    x = panel.x + 10 + c * (cell_w + margin)
                    y = panel.y + 10 + r * (cell_h + margin)
                    rect = pygame.Rect(x, y, cell_w, cell_h)
                    if i == confirmed_idx:
                        border_color = GREEN
                        border_width = 3
                    elif i == idx:
                        border_color = YELLOW
                        border_width = 2
                    else:
                        border_color = GRAY
                        border_width = 1
                    pygame.draw.rect(self.screen, border_color, rect, border_width)
                    if i < team_slots:
                        txt = names[i] or "---"
                        col = WHITE if available[i] else INACTIVE
                    elif i == team_slots:
                        txt = "?"
                        col = WHITE
                    else:
                        txt = "X"
                        col = WHITE
                    self.screen.blit(font.render(txt, True, col), (rect.x + 5, rect.y + 5))

                if team_label == "Team 1":
                    instr = "(E/D/S/F + A/Enter)" if not is_cyb1 else "(Cyborg...)"
                    y0 = panel.bottom - 5
                else:
                    instr = "(Arrows + RCtrl)" if not is_cyb2 else "(Cyborg...)"
                    y0 = panel.bottom - 5
                text_surf = font.render(instr, True, WHITE)
                self.screen.blit(text_surf, (panel.x + 10, y0))

            if need_team1:
                draw_panel(panel1, names1, available1, idx1, confirmed_idx1, "Team 1")
            if need_team2:
                draw_panel(panel2, names2, available2, idx2, confirmed_idx2, "Team 2")

            pygame.display.flip()
            clock.tick(60)

        new1 = None
        new2 = None
        if need_team1:
            if idx1 < team_slots and available1[idx1]:
                new1 = SHIP_CLASSES[names1[idx1]]
                self.last_selected_idx1 = idx1  # Сохраняем индекс выбранной ячейки
            elif idx1 == team_slots:
                choices = [i for i in self.team1_remaining]
                if choices:
                    pick = random.choice(choices)
                    new1 = SHIP_CLASSES[names1[pick]]
                    self.last_selected_idx1 = pick
        if need_team2:
            if idx2 < team_slots and available2[idx2]:
                new2 = SHIP_CLASSES[names2[idx2]]
                self.last_selected_idx2 = idx2  # Сохраняем индекс выбранной ячейки
            elif idx2 == team_slots:
                choices = [i for i in self.team2_remaining]
                if choices:
                    pick = random.choice(choices)
                    new2 = SHIP_CLASSES[names2[pick]]
                    self.last_selected_idx2 = pick

        print(f"Selected: Team 1={new1.__name__ if new1 else None}, Team 2={new2.__name__ if new2 else None}")
        return new1, new2

    def end_game(self, winner):
        font = pygame.font.SysFont("Arial", 48)
        text = font.render(f"{winner} wins!", True, (255, 255, 0))
        self.screen.fill((0, 0, 40))
        self.screen.blit(
            text,
            (
                SCREEN_W // 2 - text.get_width() // 2,
                SCREEN_H // 2 - text.get_height() // 2,
            ),
        )
        pygame.display.flip()
        pygame.time.wait(3000)
        self.menu.save_last_config()
        self.running = False

    def draw_hud(self, zoom=1.0):
        hud_rect = pygame.Rect(GAME_SCREEN_W, 0, PANEL_WIDTH, SCREEN_H)
        pygame.draw.rect(self.screen, (50, 50, 50), hud_rect)
        font = pygame.font.SysFont("Arial", 24)

        team1_name = self.config["team_names"]["Team 1"]
        team1_control = self.config["settings"]["Team 1"]["control"]
        team1_crew = self.ship1.crew if self.ship1 else 0
        team1_energy = self.ship1.energy if self.ship1 else 0
        team1_speed = int(math.hypot(self.ship1.vx, self.ship1.vy)) if self.ship1 else 0
        texts = [
            f"Team 1: {team1_name}",
            f"Crew: {team1_crew}",
            f"Energy: {team1_energy}",
            f"Speed: {team1_speed}",
            f"Ctrl: {team1_control}",
        ]
        for i, t in enumerate(texts):
            self.screen.blit(
                font.render(t, True, (255, 255, 255)),
                (GAME_SCREEN_W + 10, 10 + i * 30),
            )
        if team1_control != "Human":
            diff = self.config["settings"]["Team 1"].get("cyborg_difficulty", "N/A")
            self.screen.blit(
                font.render(f"Diff: {diff}", True, (255, 255, 255)),
                (GAME_SCREEN_W + 10, 10 + len(texts) * 30),
            )

        team2_name = self.config["team_names"]["Team 2"]
        team2_control = self.config["settings"]["Team 2"]["control"]
        team2_crew = self.ship2.crew if self.ship2 else 0
        team2_energy = self.ship2.energy if self.ship2 else 0
        team2_speed = int(math.hypot(self.ship2.vx, self.ship2.vy)) if self.ship2 else 0
        texts = [
            f"Team 2: {team2_name}",
            f"Crew: {team2_crew}",
            f"Energy: {team2_energy}",
            f"Speed: {team2_speed}",
            f"Ctrl: {team2_control}",
        ]
        for i, t in enumerate(texts):
            self.screen.blit(
                font.render(t, True, (255, 255, 255)),
                (GAME_SCREEN_W + 10, 220 + i * 30),
            )
        if team2_control != "Human":
            diff = self.config["settings"]["Team 2"].get("cyborg_difficulty", "N/A")
            self.screen.blit(
                font.render(f"Diff: {diff}", True, (255, 255, 255)),
                (GAME_SCREEN_W + 10, 220 + len(texts) * 30),
            )

    def render(self):
        from project.stars import draw_star_layer_colored
        self.screen.fill((0, 0, 0))
        zoom = 1.0
        draw_star_layer_colored(self.screen, self.star_layer_far, self.globalCamX, self.globalCamY, 0.3, zoom)
        draw_star_layer_colored(self.screen, self.star_layer_mid, self.globalCamX, self.globalCamY, 0.6, zoom)
        draw_star_layer_colored(self.screen, self.star_layer_near, self.globalCamX, self.globalCamY, 0.9, zoom)

        self.planet.draw(self.screen, self.cam, zoom)
        for asteroid in self.asteroids:
            asteroid.draw(self.screen, self.cam, zoom)
        self.ship1.draw(self.screen, self.cam, zoom)
        self.ship2.draw(self.screen, self.cam, zoom)
        for projectile in self.missiles:
            projectile.draw(self.screen, self.cam, zoom)
        self.draw_hud(zoom)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            result = self.handle_input()
            if result == "MENU":
                self.menu.save_last_config()
                return "MENU"
            self.update(dt)
            self.render()
        self.menu.save_last_config()
        return "MENU"