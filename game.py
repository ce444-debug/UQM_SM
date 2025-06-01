import pygame
import sys
import math
import random

from project.config import *
from project.utils import spawn_ship, wrap_delta, world_to_screen, wrap_position
from project.gravity import apply_gravity
from project.entities.planet import Planet
from project.entities.asteroid import Asteroid
from project.entities.camera import Camera
from project.ships import SHIP_CLASSES  # Реестр кораблей
from project.entities.mine import Plasmoid
from project.collisions import (handle_planet_collision, handle_ship_asteroid_collision,
                                handle_ship_ship_collision, handle_asteroid_collision)
from menu import PauseMenu


class Game:
    def __init__(self, config):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Combat Zone with Gravity-Boosted Ships")
        self.clock = pygame.time.Clock()

        self.config = config
        self.game_mode = config["mode"]

        self.team1_fleet = [SHIP_CLASSES[ship] for ship in config["teams"]["Team 1"] if ship is not None]
        self.team2_fleet = [SHIP_CLASSES[ship] for ship in config["teams"]["Team 2"] if ship is not None]

        if not self.team1_fleet or not self.team2_fleet:
            print("Error: One of the fleets is empty!")
            pygame.quit()
            sys.exit()

        self.team1_remaining = list(self.team1_fleet)
        self.team2_remaining = list(self.team2_fleet)

        if config["settings"]["Team 1"]["control"] == "Human":
            selected_ship = self.human_select_initial_ship("Team 1", self.team1_remaining)
            self.team1_remaining.remove(selected_ship)
            sx1, sy1 = spawn_ship()
            self.ship1 = selected_ship(sx1, sy1, (255, 100, 100))
            self.wait_for_key("Team 1 selected. Press any key for Team 2 selection.")
        else:
            selected_ship = self.team1_remaining.pop(0)
            sx1, sy1 = spawn_ship()
            self.ship1 = selected_ship(sx1, sy1, (255, 100, 100))

        if config["settings"]["Team 2"]["control"] == "Human":
            selected_ship = self.human_select_initial_ship("Team 2", self.team2_remaining)
            self.team2_remaining.remove(selected_ship)
            sx2, sy2 = spawn_ship()
            self.ship2 = selected_ship(sx2, sy2, (100, 200, 255))
            self.wait_for_key("Team 2 selected. Press any key to start round.")
        else:
            selected_ship = self.team2_remaining.pop(0)
            sx2, sy2 = spawn_ship()
            self.ship2 = selected_ship(sx2, sy2, (100, 200, 255))

        if self.game_mode != "Human vs Human":
            if self.config["settings"]["Team 2"]["control"] == "Cyborg":
                from project.ai_controller import EarthlingAIController
                self.ship2.ai_controller = EarthlingAIController(self.ship2,
                                                                 difficulty=self.config["settings"]["Team 2"][
                                                                     "cyborg_difficulty"])
            if self.config["settings"]["Team 1"]["control"] == "Cyborg":
                from project.ai_controller import EarthlingAIController
                self.ship1.ai_controller = EarthlingAIController(self.ship1,
                                                                 difficulty=self.config["settings"]["Team 1"][
                                                                     "cyborg_difficulty"])
        else:
            self.ship1.ai_controller = None
            self.ship2.ai_controller = None

        self.planet = Planet(FIELD_W / 2, FIELD_H / 2, 30, (180, 180, 180))
        self.cam = Camera(FIELD_W / 2, FIELD_H / 2)
        self.globalCamX = self.cam.x
        self.globalCamY = self.cam.y
        self.prevCamX = self.cam.x
        self.prevCamY = self.cam.y

        from project.stars import generate_colored_stars
        self.star_layer_far = generate_colored_stars(180)
        self.star_layer_mid = generate_colored_stars(120)
        self.star_layer_near = generate_colored_stars(80)

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

    def pre_round_ship_selection(self):
        if self.config["settings"]["Team 1"]["control"] == "Human":
            if self.team1_remaining:
                selected_ship = self.human_select_initial_ship("Team 1", self.team1_remaining)
                self.team1_remaining.remove(selected_ship)
                sx, sy = spawn_ship()
                self.ship1 = selected_ship(sx, sy, (255, 100, 100))
                self.wait_for_key("Team 1 replacement selected. Press any key for Team 2 replacement.")
        else:
            if self.team1_remaining:
                selected_ship = self.team1_remaining.pop(0)
                sx, sy = spawn_ship()
                self.ship1 = selected_ship(sx, sy, (255, 100, 100))
        if self.config["settings"]["Team 2"]["control"] == "Human":
            if self.team2_remaining:
                selected_ship = self.human_select_initial_ship("Team 2", self.team2_remaining)
                self.team2_remaining.remove(selected_ship)
                sx, sy = spawn_ship()
                self.ship2 = selected_ship(sx, sy, (100, 200, 255))
                self.wait_for_key("Team 2 replacement selected. Press any key to continue round.")
        else:
            if self.team2_remaining:
                selected_ship = self.team2_remaining.pop(0)
                sx, sy = spawn_ship()
                self.ship2 = selected_ship(sx, sy, (100, 200, 255))

    def wait_for_key(self, message):
        waiting = True
        font = pygame.font.SysFont("Arial", 36)
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    waiting = False
            self.screen.fill((0, 0, 0))
            text = font.render(message, True, (255, 255, 255))
            self.screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, SCREEN_H // 2 - text.get_height() // 2))
            pygame.display.flip()
            self.clock.tick(30)

    def human_select_initial_ship(self, team, available_ships):
        options = available_ships
        selected = 0
        selecting = True
        font = pygame.font.SysFont("Arial", 36)
        while selecting:
            self.screen.fill((0, 0, 40))
            title = font.render(f"{team} - Select Your Ship", True, (255, 255, 0))
            self.screen.blit(title, (50, 50))
            for i, ship_class in enumerate(options):
                text = ship_class.__name__
                color = (255, 255, 0) if i == selected else (200, 200, 200)
                option_text = pygame.font.SysFont("Arial", 30).render(f"{i + 1}. {text}", True, color)
                self.screen.blit(option_text, (50, 100 + i * 40))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(options)
                    elif event.key == pygame.K_RETURN:
                        selecting = False
                        return options[selected]
                    elif event.key == pygame.K_ESCAPE:
                        selecting = False
                        return options[0]
        return options[0]

    def pause(self):
        pause_menu = PauseMenu(self.screen, self.clock)
        option = pause_menu.display()
        return option

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    option = self.pause()
                    if option == "Resume":
                        continue
                    elif option == "Main Menu":
                        self.running = False
                    elif event.key == pygame.K_x:
                        pygame.quit()
                        sys.exit()
                if not (hasattr(self.ship1, 'ai_controller') and self.ship1.ai_controller is not None):
                    if event.key == pygame.K_a:
                        primary = self.ship1.fire_primary(self.ship2, self.game_time)
                        if primary:
                            if isinstance(primary, list):
                                self.missiles.extend(primary)
                            else:
                                self.missiles.append(primary)
                    if event.key == pygame.K_q:
                        special = self.ship1.fire_secondary([self.ship2] + self.asteroids + self.missiles,
                                                            self.game_time)
                        if special:
                            if isinstance(special, list):
                                self.missiles.extend(special)
                            else:
                                self.missiles.append(special)
                if not (hasattr(self.ship2, 'ai_controller') and self.ship2.ai_controller is not None):
                    if event.key == pygame.K_RCTRL:
                        primary = self.ship2.fire_primary(self.ship1, self.game_time)
                        if primary:
                            if isinstance(primary, list):
                                self.missiles.extend(primary)
                            else:
                                self.missiles.append(primary)
                    if event.key == pygame.K_RSHIFT:
                        special = self.ship2.fire_secondary([self.ship1] + self.asteroids + self.missiles,
                                                            self.game_time)
                        if special:
                            if isinstance(special, list):
                                self.missiles.extend(special)
                            else:
                                self.missiles.append(special)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    if hasattr(self.ship1, 'release_mine'):
                        mine = self.ship1.release_mine()
                        if mine and mine not in self.missiles:
                            self.missiles.append(mine)
                if event.key == pygame.K_RCTRL:
                    if hasattr(self.ship2, 'release_mine'):
                        mine = self.ship2.release_mine()
                        if mine and mine not in self.missiles:
                            self.missiles.append(mine)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            if hasattr(self.ship1, 'current_mine') and self.ship1.current_mine is not None:
                if self.ship1.current_mine not in self.missiles:
                    self.missiles.append(self.ship1.current_mine)
        if keys[pygame.K_RCTRL]:
            if hasattr(self.ship2, 'current_mine') and self.ship2.current_mine is not None:
                if self.ship2.current_mine not in self.missiles:
                    self.missiles.append(self.ship2.current_mine)
        if (not hasattr(self.ship1, 'ai_controller')) or (self.ship1.ai_controller is None):
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
                    if speed > self.ship1.max_thrust and (speed > 0 and (
                            self.ship1.vx * thrust_dx + self.ship1.vy * thrust_dy) / speed > 0) and not self.ship1.in_gravity_field:
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
        if (not hasattr(self.ship2, 'ai_controller')) or (self.ship2.ai_controller is None):
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
                    if speed > self.ship2.max_thrust and (speed > 0 and (
                            self.ship2.vx * thrust_dx + self.ship2.vy * thrust_dy) / speed > 0) and not self.ship2.in_gravity_field:
                        self.ship2.thrust_timer -= self.ship2.thrust_wait
                        continue
                    if (self.ship2.vx * thrust_dx + self.ship2.vy * thrust_dy) / max(speed, 1) < 0:
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
            if hasattr(projectile, 'launching') and projectile.launching:
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
                target_radius = getattr(projectile.target, 'radius', 0)
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
                if abs(projectile.x - asteroid.x) > (projectile.radius + asteroid.radius) or abs(
                        projectile.y - asteroid.y) > (projectile.radius + asteroid.radius):
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
                if hasattr(proj1, "owner") and hasattr(proj2,
                                                       "owner") and proj1.owner is not None and proj2.owner is not None:
                    if proj1.owner.id != proj2.owner.id:
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
            if sx < -margin or sx > GAME_SCREEN_W + margin or sy < -margin or sy > SCREEN_H + margin:
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
        if self.ship1 and self.ship1.dead:
            new_ship_class = self.get_replacement("Team 1")
            if new_ship_class is None:
                self.end_game(winner="Team 2")
                return
            else:
                sx, sy = spawn_ship()
                self.ship1 = new_ship_class(sx, sy, (255, 100, 100))
                if self.config["settings"]["Team 1"]["control"] == "Human":
                    self.wait_for_key("Team 1 replacement selected. Press any key to continue round.")
        if self.ship2 and self.ship2.dead:
            new_ship_class = self.get_replacement("Team 2")
            if new_ship_class is None:
                self.end_game(winner="Team 1")
                return
            else:
                sx, sy = spawn_ship()
                self.ship2 = new_ship_class(sx, sy, (100, 200, 255))
                if self.config["settings"]["Team 2"]["control"] == "Human":
                    self.wait_for_key("Team 2 replacement selected. Press any key to continue round.")

    # Изменения: Новый метод get_replacement с использованием нового меню выбора
    def get_replacement(self, team):
        if team == "Team 1":
            if self.team1_remaining:
                if self.config["settings"]["Team 1"]["control"] == "Human":
                    new_ship_class = self.select_replacement_ship("Team 1", self.team1_remaining, is_cyborg=False)
                    self.team1_remaining.remove(new_ship_class)
                    return new_ship_class
                else:
                    new_ship_class = self.select_replacement_ship("Team 1", self.team1_remaining, is_cyborg=True)
                    self.team1_remaining.remove(new_ship_class)
                    return new_ship_class
            else:
                return None
        elif team == "Team 2":
            if self.team2_remaining:
                if self.config["settings"]["Team 2"]["control"] == "Human":
                    new_ship_class = self.select_replacement_ship("Team 2", self.team2_remaining, is_cyborg=False)
                    self.team2_remaining.remove(new_ship_class)
                    return new_ship_class
                else:
                    new_ship_class = self.select_replacement_ship("Team 2", self.team2_remaining, is_cyborg=True)
                    self.team2_remaining.remove(new_ship_class)
                    return new_ship_class
            else:
                return None

    # Изменения: Новая функция для выбора корабля замены
    def select_replacement_ship(self, team, available_ships, is_cyborg):
        available_names = []
        for cls in available_ships:
            for key, value in SHIP_CLASSES.items():
                if value == cls:
                    available_names.append(key)
                    break
        if not available_names:
            return None
        if is_cyborg:
            chosen_name = "?"
        else:
            chosen_name = self.open_ship_selection_menu(available_names)
        if chosen_name == "?":
            chosen_name = random.choice(available_names)
        return SHIP_CLASSES.get(chosen_name, None)

    # Изменения: Новая функция, открывающая меню выбора корабля для замены
    def open_ship_selection_menu(self, available_names):
        ship_list = available_names + ["?"]
        selected_index = 0
        running = True
        YELLOW = (255, 255, 0)
        WHITE = (255, 255, 255)
        GRAY = (200, 200, 200)
        font_title = pygame.font.SysFont("Arial", 48)
        font_menu = pygame.font.SysFont("Arial", 36)
        font_small = pygame.font.SysFont("Arial", 24)
        while running:
            self.screen.fill((20, 20, 60))
            title = font_title.render("Select Replacement Ship", True, YELLOW)
            self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 20))
            info = font_small.render("Use arrows, Enter to select, Esc to cancel", True, WHITE)
            self.screen.blit(info, (50, SCREEN_H - 40))
            list_x = SCREEN_W // 2 - 100
            list_y = 100
            for i, ship in enumerate(ship_list):
                color = YELLOW if i == selected_index else GRAY
                ship_text = font_menu.render(ship, True, color)
                self.screen.blit(ship_text, (list_x, list_y + i * 40))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(ship_list)
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(ship_list)
                    elif event.key == pygame.K_RETURN:
                        running = False
                        return ship_list[selected_index]
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                        return ship_list[0]
            self.clock.tick(30)

    def end_game(self, winner):
        font = pygame.font.SysFont("Arial", 48)
        text = font.render(f"{winner} wins!", True, (255, 255, 0))
        self.screen.fill((0, 0, 40))
        self.screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, SCREEN_H // 2 - text.get_height() // 2))
        pygame.display.flip()
        pygame.time.wait(3000)
        self.running = False

    # Изменения: Новая версия функции draw_hud с добавлением энергии, скорости и сложности для Cyborg
    def draw_hud(self, zoom=1.0):
        hud_rect = pygame.Rect(GAME_SCREEN_W, 0, PANEL_WIDTH, SCREEN_H)
        pygame.draw.rect(self.screen, (50, 50, 50), hud_rect)  # Фон HUD
        font = pygame.font.SysFont("Arial", 24)

        # Информация для Team 1
        team1_name = self.config["team_names"]["Team 1"]
        team1_control = self.config["settings"]["Team 1"]["control"]
        team1_crew = self.ship1.crew if self.ship1 else 0
        team1_energy = self.ship1.energy if self.ship1 else 0
        team1_speed = int(math.hypot(self.ship1.vx, self.ship1.vy)) if self.ship1 else 0
        text1 = font.render(f"Team 1: {team1_name}", True, (255, 255, 255))
        text2 = font.render(f"Crew: {team1_crew}", True, (255, 255, 255))
        text3 = font.render(f"Energy: {team1_energy}", True, (255, 255, 255))
        text4 = font.render(f"Speed: {team1_speed}", True, (255, 255, 255))
        text5 = font.render(f"Ctrl: {team1_control}", True, (255, 255, 255))
        self.screen.blit(text1, (GAME_SCREEN_W + 10, 10))
        self.screen.blit(text2, (GAME_SCREEN_W + 10, 40))
        self.screen.blit(text3, (GAME_SCREEN_W + 10, 70))
        self.screen.blit(text4, (GAME_SCREEN_W + 10, 100))
        self.screen.blit(text5, (GAME_SCREEN_W + 10, 130))
        if team1_control != "Human Control":
            team1_diff = self.config["settings"]["Team 1"].get("cyborg_difficulty", "N/A")
            text6 = font.render(f"Diff: {team1_diff}", True, (255, 255, 255))
            self.screen.blit(text6, (GAME_SCREEN_W + 10, 160))

        # Информация для Team 2
        team2_name = self.config["team_names"]["Team 2"]
        team2_control = self.config["settings"]["Team 2"]["control"]
        team2_crew = self.ship2.crew if self.ship2 else 0
        team2_energy = self.ship2.energy if self.ship2 else 0
        team2_speed = int(math.hypot(self.ship2.vx, self.ship2.vy)) if self.ship2 else 0
        text7 = font.render(f"Team 2: {team2_name}", True, (255, 255, 255))
        text8 = font.render(f"Crew: {team2_crew}", True, (255, 255, 255))
        text9 = font.render(f"Energy: {team2_energy}", True, (255, 255, 255))
        text10 = font.render(f"Speed: {team2_speed}", True, (255, 255, 255))
        text11 = font.render(f"Ctrl: {team2_control}", True, (255, 255, 255))
        self.screen.blit(text7, (GAME_SCREEN_W + 10, 220))
        self.screen.blit(text8, (GAME_SCREEN_W + 10, 250))
        self.screen.blit(text9, (GAME_SCREEN_W + 10, 280))
        self.screen.blit(text10, (GAME_SCREEN_W + 10, 310))
        self.screen.blit(text11, (GAME_SCREEN_W + 10, 340))
        if team2_control != "Human Control":
            team2_diff = self.config["settings"]["Team 2"].get("cyborg_difficulty", "N/A")
            text12 = font.render(f"Diff: {team2_diff}", True, (255, 255, 255))
            self.screen.blit(text12, (GAME_SCREEN_W + 10, 370))

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
            self.handle_input()
            self.update(dt)
            self.render()
        pygame.quit()
