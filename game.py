import pygame
import sys
import math
import random

from project.config import *
from project.utils import spawn_ship, wrap_delta, world_to_screen
from project.gravity import apply_gravity
from project.entities.planet import Planet
from project.entities.asteroid import Asteroid
from project.entities.camera import Camera
from project.ships import SHIP_CLASSES  # Реестр кораблей
from project.entities.mine import Plasmoid
from project.collisions import (handle_planet_collision, handle_ship_asteroid_collision,
                                handle_ship_ship_collision, handle_asteroid_collision)
from project.stars import generate_colored_stars, draw_star_layer_colored
from ai_controller import EarthlingAIController, KohrAhAIController
from menu import PauseMenu, MainMenu, ModeMenu, DifficultyMenu
from project.ships.base_ship import BaseShip
from world import World  # Класс World вынесен в отдельный файл

def generate_offscreen_asteroid(cam, zoom):
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
    new_ast.angular_velocity = ASTEROID_ROTATION_AXIS * random.uniform(50, 180)
    return new_ast

# Функции для обработки вращения и ускорения для игрока
def process_rotation(ship, dt, direction):
    ship.angle = (ship.angle + direction * ship.turn_speed * dt) % 360

def process_acceleration(ship, dt):
    if not hasattr(ship, "thrust_timer"):
        ship.thrust_timer = 0
    ship.thrust_timer += dt
    while ship.thrust_timer >= ship.thrust_wait:
        rad = math.radians(ship.angle)
        thrust_dx = math.sin(rad)
        thrust_dy = -math.cos(rad)
        speed = math.hypot(ship.vx, ship.vy)
        if speed > ship.max_thrust and speed > 0 and (ship.vx * thrust_dx + ship.vy * thrust_dy) / speed > 0 and not ship.in_gravity_field:
            ship.thrust_timer -= ship.thrust_wait
            continue
        if (ship.vx * thrust_dx + ship.vy * thrust_dy) / max(speed, 1) < 0:
            braking_multiplier = 2.0
            ship.vx += braking_multiplier * ship.thrust_increment * thrust_dx
            ship.vy += braking_multiplier * ship.thrust_increment * thrust_dy
        else:
            ship.vx += ship.thrust_increment * thrust_dx
            ship.vy += ship.thrust_increment * thrust_dy
        ship.thrust_timer -= ship.thrust_wait

def play_again_menu(screen, clock):
    font = pygame.font.SysFont("Arial", 36)
    options = ["Play Again", "Exit"]
    selected = 0
    running = True
    while running:
        screen.fill((0, 0, 40))
        title = font.render("Play Again?", True, (255, 255, 255))
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 50))
        for i, option in enumerate(options):
            color = (255, 255, 0) if i == selected else (200, 200, 200)
            text = font.render(option, True, color)
            screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 150 + i * 50))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Exit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return options[selected]
        clock.tick(30)

class Game:
    def __init__(self, game_mode="Multiplayer", difficulty="Medium"):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Combat Zone with Gravity-Boosted Ships")
        self.clock = pygame.time.Clock()

        # Выбор кораблей для игроков
        self.ship_class1 = self.ship_selection_screen(1)
        self.ship_class2 = self.ship_selection_screen(2)
        sx1, sy1 = spawn_ship()
        sx2, sy2 = spawn_ship()
        self.ship1 = self.ship_class1(sx1, sy1, (255, 100, 100))
        self.ship2 = self.ship_class2(sx2, sy2, (100, 200, 255))

        # Режим одиночной игры: назначаем ИИ для одного из кораблей
        self.game_mode = game_mode
        self.difficulty = difficulty
        if self.game_mode == "Single Player":
            if self.ship2.name in ["Earthling Cruiser"]:
                self.ship2.ai_controller = EarthlingAIController(self.ship2, difficulty=self.difficulty)
            elif self.ship2.name in ["KOHR-AH MARAUDER"]:
                self.ship2.ai_controller = KohrAhAIController(self.ship2, difficulty=self.difficulty)
            else:
                self.ship2.ai_controller = None
        else:
            self.ship1.ai_controller = None
            self.ship2.ai_controller = None

        self.planet = Planet(FIELD_W / 2, FIELD_H / 2, 30, (180, 180, 180))
        self.cam = Camera(FIELD_W / 2, FIELD_H / 2)
        self.globalCamX = self.cam.x
        self.globalCamY = self.cam.y
        self.prevCamX = self.cam.x
        self.prevCamY = self.cam.y

        self.star_layer_far = generate_colored_stars(180)
        self.star_layer_mid = generate_colored_stars(120)
        self.star_layer_near = generate_colored_stars(80)

        # Создаем объект World и добавляем корабли и астероиды
        self.world = World()
        self.world.add(self.ship1)
        self.world.add(self.ship2)
        for _ in range(5):
            x = random.uniform(0, FIELD_W)
            y = random.uniform(0, FIELD_H)
            radius = random.randint(8, 12)
            vx = random.uniform(-50, 50)
            vy = random.uniform(-50, 50)
            color = (200, 200, 200)
            asteroid = Asteroid(x, y, radius, vx, vy, color)
            self.world.add(asteroid)

        self.running = True
        self.dt = 0
        self.game_over = False
        self.winner = None

        # Настройки управления для игроков через словари
        self.players = [
            {
                "ship": self.ship1,
                "enemy": self.ship2,
                "keys": {
                    "rotate_left": pygame.K_s,
                    "rotate_right": pygame.K_f,
                    "accelerate": pygame.K_e,
                    "fire_primary": pygame.K_a,
                    "fire_secondary": pygame.K_q,
                    "release_mine": pygame.K_a  # используется при KEYUP
                }
            },
            {
                "ship": self.ship2,
                "enemy": self.ship1,
                "keys": {
                    "rotate_left": pygame.K_LEFT,
                    "rotate_right": pygame.K_RIGHT,
                    "accelerate": pygame.K_UP,
                    "fire_primary": pygame.K_RCTRL,
                    "fire_secondary": pygame.K_RSHIFT,
                    "release_mine": pygame.K_RCTRL  # используется при KEYUP
                }
            }
        ]

    def ship_selection_screen(self, player_number):
        font = pygame.font.SysFont("Arial", 24)
        selected_index = 0
        ship_names = list(SHIP_CLASSES.keys())
        selecting = True
        while selecting:
            self.screen.fill((0, 0, 40))
            title = font.render(f"Player {player_number}: Choose your ship", True, (255, 255, 255))
            self.screen.blit(title, (50, 50))
            for idx, name in enumerate(ship_names):
                color = (255, 255, 0) if idx == selected_index else (200, 200, 200)
                text = font.render(name, True, color)
                self.screen.blit(text, (100, 150 + idx * 30))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(ship_names)
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(ship_names)
                    elif event.key == pygame.K_RETURN:
                        selecting = False
                        return SHIP_CLASSES[ship_names[selected_index]]
            self.clock.tick(30)

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
                    elif option == "Exit":
                        pygame.quit()
                        sys.exit()
                for player in self.players:
                    ship = player["ship"]
                    if hasattr(ship, "ai_controller") and ship.ai_controller:
                        continue
                    keys_map = player["keys"]
                    if event.key == keys_map["fire_primary"]:
                        result = ship.fire_primary(player["enemy"], self.world.game_time)
                        if result:
                            if isinstance(result, list):
                                for obj in result:
                                    self.world.add(obj)
                            else:
                                self.world.add(result)
                    if event.key == keys_map["fire_secondary"]:
                        result = ship.fire_secondary(
                            [player["enemy"]] + self.world.filter_entities(lambda e: isinstance(e, Asteroid)) +
                            self.world.filter_entities(lambda e: hasattr(e, "damage")),
                            self.world.game_time)
                        if result:
                            if isinstance(result, list):
                                for obj in result:
                                    self.world.add(obj)
                            else:
                                self.world.add(result)
            elif event.type == pygame.KEYUP:
                for player in self.players:
                    ship = player["ship"]
                    if event.key == player["keys"]["release_mine"]:
                        if hasattr(ship, 'release_mine'):
                            mine = ship.release_mine()
                            if mine:
                                self.world.add(mine)
        pressed = pygame.key.get_pressed()
        for player in self.players:
            ship = player["ship"]
            if hasattr(ship, "ai_controller") and ship.ai_controller:
                continue
            keys_map = player["keys"]
            if pressed[keys_map["rotate_left"]]:
                process_rotation(ship, self.dt, -1)
            if pressed[keys_map["rotate_right"]]:
                process_rotation(ship, self.dt, +1)
            if pressed[keys_map["accelerate"]]:
                process_acceleration(ship, self.dt)

    def update(self, dt):
        self.dt = dt
        self.world.update(dt)

        self.ship1.in_gravity_field = False
        self.ship2.in_gravity_field = False

        for player in self.players:
            ship = player["ship"]
            enemy = player["enemy"]
            if hasattr(ship, "ai_controller") and ship.ai_controller is not None:
                ship.ai_controller.update(dt, enemy,
                    self.world.filter_entities(lambda e: isinstance(e, Asteroid)) + [self.planet],
                    self.world.filter_entities(lambda e: hasattr(e, "damage")))
        apply_gravity(self.ship1, self.planet, dt)
        apply_gravity(self.ship2, self.planet, dt)
        for entity in self.world.entities:
            if hasattr(entity, 'launching') and entity.launching:
                apply_gravity(entity, self.planet, dt)

        collision_distance_margin = 100
        from project.entities.projectile import Projectile
        missiles = [e for e in self.world.entities if isinstance(e, Projectile)]
        asteroids = [e for e in self.world.entities if isinstance(e, Asteroid)]

        for i in range(len(missiles)):
            proj1 = missiles[i]
            if not proj1.active:
                continue
            if hasattr(proj1, "target") and proj1.target is not None:
                tx = proj1.target.x
                ty = proj1.target.y
                d_x = wrap_delta(proj1.x, tx, FIELD_W)
                d_y = wrap_delta(proj1.y, ty, FIELD_H)
                target_radius = getattr(proj1.target, 'radius', 0)
                if math.hypot(d_x, d_y) < (proj1.radius + target_radius):
                    proj1.target.take_damage(proj1.damage)
                    proj1.active = False
                    continue
            elif hasattr(proj1, "owner") and proj1.owner is not None:
                if proj1.owner.id == self.ship1.id:
                    enemy = self.ship2
                else:
                    enemy = self.ship1
                d_x = wrap_delta(proj1.x, enemy.x, FIELD_W)
                d_y = wrap_delta(proj1.y, enemy.y, FIELD_H)
                if math.hypot(d_x, d_y) < (proj1.radius + enemy.radius):
                    enemy.take_damage(proj1.damage)
                    proj1.active = False
                    continue
            for asteroid in asteroids:
                if abs(proj1.x - asteroid.x) > collision_distance_margin or abs(proj1.y - asteroid.y) > collision_distance_margin:
                    continue
                dx = wrap_delta(proj1.x, asteroid.x, FIELD_W)
                dy = wrap_delta(proj1.y, asteroid.y, FIELD_H)
                if math.hypot(dx, dy) < (proj1.radius + asteroid.radius):
                    asteroid.active = False
                    proj1.active = False
                    break
            dx = wrap_delta(proj1.x, self.planet.x, FIELD_W)
            dy = wrap_delta(proj1.y, self.planet.y, FIELD_H)
            if math.hypot(dx, dy) < (proj1.radius + self.planet.radius):
                proj1.active = False

        for i in range(len(missiles)):
            for j in range(i + 1, len(missiles)):
                proj1 = missiles[i]
                proj2 = missiles[j]
                if not proj1.active or not proj2.active:
                    continue
                if hasattr(proj1, "owner") and hasattr(proj2, "owner") and proj1.owner is not None and proj2.owner is not None:
                    if proj1.owner.id == proj2.owner.id:
                        continue
                if abs(proj1.x - proj2.x) > collision_distance_margin or abs(proj1.y - proj2.y) > collision_distance_margin:
                    continue
                dx = wrap_delta(proj1.x, proj2.x, FIELD_W)
                dy = wrap_delta(proj1.y, proj2.y, FIELD_H)
                if math.hypot(dx, dy) <= (proj1.radius + proj2.radius):
                    proj1.active = False
                    proj2.active = False

        for i in range(len(asteroids)):
            for j in range(i + 1, len(asteroids)):
                a1 = asteroids[i]
                a2 = asteroids[j]
                if not a1.active or not a2.active:
                    continue
                if abs(a1.x - a2.x) > collision_distance_margin or abs(a1.y - a2.y) > collision_distance_margin:
                    continue
                dx = wrap_delta(a1.x, a2.x, FIELD_W)
                dy = wrap_delta(a1.y, a2.y, FIELD_H)
                if math.hypot(dx, dy) < (a1.radius + a2.radius):
                    if dx == 0 and dy == 0:
                        nx, ny = 1.0, 0.0
                    else:
                        nx = dx / math.hypot(dx, dy)
                        ny = dy / math.hypot(dx, dy)
                    overlap = (a1.radius + a2.radius) - math.hypot(dx, dy)
                    a1.x += nx * (overlap / 2)
                    a1.y += ny * (overlap / 2)
                    a2.x -= nx * (overlap / 2)
                    a2.y -= ny * (overlap / 2)
                    dvx = a1.vx - a2.vx
                    dvy = a1.vy - a2.vy
                    p = dvx * nx + dvy * ny
                    a1.vx -= p * nx
                    a1.vy -= p * ny
                    a2.vx += p * nx
                    a2.vy += p * ny

        self.world.cleanup()

        handle_planet_collision(self.ship1, self.planet, self.world.game_time)
        handle_planet_collision(self.ship2, self.planet, self.world.game_time)
        for asteroid in asteroids:
            handle_ship_asteroid_collision(self.ship1, asteroid)
            handle_ship_asteroid_collision(self.ship2, asteroid)
        handle_ship_ship_collision(self.ship1, self.ship2)
        for i in range(len(asteroids)):
            for j in range(i + 1, len(asteroids)):
                handle_asteroid_collision(asteroids[i], asteroids[j])
        for i, asteroid in enumerate(asteroids):
            dx = wrap_delta(asteroid.x, self.planet.x, FIELD_W)
            dy = wrap_delta(asteroid.y, self.planet.y, FIELD_H)
            if math.hypot(dx, dy) < (self.planet.radius + asteroid.radius):
                new_ast = generate_offscreen_asteroid(self.cam, 1.0)
                if asteroid in self.world.entities:
                    self.world.entities.remove(asteroid)
                self.world.add(new_ast)

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

        # Проверка завершения игры
        if not self.ship1.alive or not self.ship2.alive:
            self.game_over = True
            self.running = False
            self.winner = self.ship1 if self.ship1.alive else self.ship2

    def render(self):
        d_x = wrap_delta(self.ship1.x, self.ship2.x, FIELD_W)
        d_y = wrap_delta(self.ship1.y, self.ship2.y, FIELD_H)
        ship_distance = math.hypot(d_x, d_y)
        desired_visible_width = max(ship_distance * MARGIN, MIN_VISIBLE_WIDTH)
        desired_visible_width = min(desired_visible_width, GAME_SCREEN_W)
        zoom = GAME_SCREEN_W / desired_visible_width

        self.screen.fill((0, 0, 40))
        draw_star_layer_colored(self.screen, self.star_layer_far, self.globalCamX, self.globalCamY, 0.3, zoom)
        draw_star_layer_colored(self.screen, self.star_layer_mid, self.globalCamX, self.globalCamY, 0.6, zoom)
        draw_star_layer_colored(self.screen, self.star_layer_near, self.globalCamX, self.globalCamY, 1.0, zoom)

        px, py = world_to_screen(self.planet.x, self.planet.y, self.cam.x, self.cam.y, zoom)
        pygame.draw.circle(self.screen, self.planet.color, (px, py), int(self.planet.radius * zoom))

        self.world.draw(self.screen, self.cam, zoom)

        panel_rect = pygame.Rect(GAME_SCREEN_W, 0, PANEL_WIDTH, SCREEN_H)
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect)
        x_panel = GAME_SCREEN_W + 10
        y_panel = 10
        font_panel = pygame.font.SysFont("Arial", 18)
        text = font_panel.render(self.ship1.name, True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Crew: {self.ship1.crew}/{self.ship1.max_crew}", True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Energy: {self.ship1.energy}", True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Speed: {math.hypot(self.ship1.vx, self.ship1.vy):.2f}", True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize() * 2
        text = font_panel.render(self.ship2.name, True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Crew: {self.ship2.crew}/{self.ship2.max_crew}", True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Energy: {self.ship2.energy}", True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Speed: {math.hypot(self.ship2.vx, self.ship2.vy):.2f}", True, (255, 255, 255))
        self.screen.blit(text, (x_panel, y_panel))

        pygame.display.flip()

    def display_game_over(self):
        winner = self.winner
        font = pygame.font.SysFont("Arial", 36)
        text = font.render(f"Game Over! Winner: {winner.name}", True, (255, 255, 0))
        self.screen.fill((0, 0, 40))
        self.screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, SCREEN_H // 2 - text.get_height() // 2))
        pygame.display.flip()
        pygame.time.wait(3000)

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_input()
            self.update(dt)
            self.render()
        if self.game_over:
            self.display_game_over()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    main_menu = MainMenu(screen, clock)
    option = main_menu.display()
    if option == "Exit":
        pygame.quit()
        return
    elif option == "Settings":
        pass

    mode_menu = ModeMenu(screen, clock)
    mode_option = mode_menu.display()
    if mode_option == "Back" or mode_option == "Exit":
        pygame.quit()
        return

    difficulty = "Medium"
    if mode_option == "Single Player":
        diff_menu = DifficultyMenu(screen, clock)
        diff_option = diff_menu.display()
        if diff_option == "Back" or diff_option == "Exit":
            pygame.quit()
            return
        difficulty = diff_option

    while True:
        game = Game(game_mode=mode_option, difficulty=difficulty)
        game.run()
        choice = play_again_menu(screen, clock)
        if choice == "Play Again":
            continue
        else:
            break
    pygame.quit()

if __name__ == "__main__":
    main()
