# main.py
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
from project.ships import SHIP_CLASSES  # Импорт реестра кораблей из __init__.py в пакете ships
from project.entities.mine import Plasmoid  # Для проверки типа плазмоида

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Combat Zone with Gravity-Boosted Ships")
clock = pygame.time.Clock()


def ship_selection_screen(player_number):
    font = pygame.font.SysFont("Arial", 24)
    selected_index = 0
    ship_names = list(SHIP_CLASSES.keys())
    running = True
    while running:
        screen.fill((0, 0, 40))
        title = font.render(f"Player {player_number}: Choose your ship", True, (255, 255, 255))
        screen.blit(title, (50, 50))

        for idx, name in enumerate(ship_names):
            color = (255, 255, 0) if idx == selected_index else (200, 200, 200)
            text = font.render(name, True, color)
            screen.blit(text, (100, 150 + idx * 30))

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
                    return SHIP_CLASSES[ship_names[selected_index]]
        clock.tick(30)


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


def main():
    # Выбор кораблей для игроков
    ShipClass1 = ship_selection_screen(1)
    ShipClass2 = ship_selection_screen(2)

    sx1, sy1 = spawn_ship()
    sx2, sy2 = spawn_ship()
    ship1 = ShipClass1(sx1, sy1, (255, 100, 100))
    ship2 = ShipClass2(sx2, sy2, (100, 200, 255))

    planet = Planet(FIELD_W / 2, FIELD_H / 2, 30, (180, 180, 180))
    cam = Camera(FIELD_W / 2, FIELD_H / 2)
    globalCamX = cam.x
    globalCamY = cam.y
    prevCamX = cam.x
    prevCamY = cam.y

    from project.stars import generate_colored_stars, draw_star_layer_colored
    star_layer_far = generate_colored_stars(180)
    star_layer_mid = generate_colored_stars(120)
    star_layer_near = generate_colored_stars(80)

    asteroids = []
    for _ in range(5):
        x = random.uniform(0, FIELD_W)
        y = random.uniform(0, FIELD_H)
        radius = random.randint(8, 12)
        vx = random.uniform(-50, 50)
        vy = random.uniform(-50, 50)
        color = (200, 200, 200)
        asteroids.append(Asteroid(x, y, radius, vx, vy, color))

    missiles = []
    game_time = 0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        game_time += dt

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                # Обработка для Ship2 (второй корабль)
                if event.key == pygame.K_RCTRL:
                    # Если корабль поддерживает систему мин (например, KOHR-AH MARAUDER)
                    if hasattr(ship2, 'start_mine_launch'):
                        ship2.start_mine_launch(ship1, game_time)
                    # Если это YEHAT TERMINATOR, вызываем его ion cannon
                    elif ship2.name == "YEHAT TERMINATOR":
                        missiles.extend(ship2.fire_missile(ship1, game_time))
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RCTRL:
                    if hasattr(ship2, 'release_mine'):
                        mine = ship2.release_mine()
                        if mine:
                            missiles.append(mine)

        keys = pygame.key.get_pressed()

        # Управление для Ship1 (Player 1): S - налево, F - направо, E - ускорение
        if keys[pygame.K_s]:
            ship1.angle = (ship1.angle - ship1.turn_speed * dt) % 360
        if keys[pygame.K_f]:
            ship1.angle = (ship1.angle + ship1.turn_speed * dt) % 360
        if keys[pygame.K_e]:
            rad = math.radians(ship1.angle)
            a = ship1.thrust_increment / ship1.thrust_wait
            ship1.vx += a * dt * math.sin(rad)
            ship1.vy -= a * dt * math.cos(rad)
            current_speed = math.hypot(ship1.vx, ship1.vy)
            if current_speed > ship1.max_thrust:
                factor = ship1.max_thrust / current_speed
                ship1.vx *= factor
                ship1.vy *= factor

        # Ship1 оружие: A (основное) и Q (специальное)
        if keys[pygame.K_a]:
            missile = ship1.fire_missile(ship2, game_time)
            if missile:
                missiles.append(missile)
        if keys[pygame.K_q]:
            # Для Ship1 требуется передать список целей
            ship1.fire_laser_defense([ship2] + asteroids + missiles, game_time)

        # Управление для Ship2 (Player 2): стрелки для движения
        if keys[pygame.K_LEFT]:
            ship2.angle = (ship2.angle - ship2.turn_speed * dt) % 360
        if keys[pygame.K_RIGHT]:
            ship2.angle = (ship2.angle + ship2.turn_speed * dt) % 360
        if keys[pygame.K_UP]:
            rad = math.radians(ship2.angle)
            a = ship2.thrust_increment / ship2.thrust_wait
            ship2.vx += a * dt * math.sin(rad)
            ship2.vy -= a * dt * math.cos(rad)
            current_speed = math.hypot(ship2.vx, ship2.vy)
            if current_speed > ship2.max_thrust:
                factor = ship2.max_thrust / current_speed
                ship2.vx *= factor
                ship2.vy *= factor

        # Ship2 оружие: RSHIFT для плазмоидного кольца (если применимо)
        if keys[pygame.K_RSHIFT]:
            new_plasmoids = ship2.fire_laser_defense(game_time)
            if new_plasmoids:
                missiles.extend(new_plasmoids)

        ship1.update(dt)
        ship2.update(dt)
        for asteroid in asteroids:
            asteroid.update(dt)

        # Обработка столкновений для снарядов, имеющих target и target не None
        for projectile in missiles:
            projectile.update(dt)
            if projectile.active and hasattr(projectile, "target") and projectile.target is not None:
                d_x = wrap_delta(projectile.x, projectile.target.x, FIELD_W)
                d_y = wrap_delta(projectile.y, projectile.target.y, FIELD_H)
                if math.hypot(d_x, d_y) < (projectile.radius + projectile.target.radius):
                    projectile.target.take_damage(projectile.damage)
                    projectile.active = False

        # Обработка столкновений для плазмоидов
        for projectile in missiles:
            if projectile.active and isinstance(projectile, Plasmoid):
                # Если владелец определён, проверяем столкновение с вражеским кораблём
                if projectile.owner is not None:
                    if projectile.owner == ship1 and ship2.active:
                        d_x = wrap_delta(projectile.x, ship2.x, FIELD_W)
                        d_y = wrap_delta(projectile.y, ship2.y, FIELD_H)
                        if math.hypot(d_x, d_y) < (projectile.radius + ship2.radius):
                            ship2.take_damage(projectile.damage)
                            projectile.active = False
                    elif projectile.owner == ship2 and ship1.active:
                        d_x = wrap_delta(projectile.x, ship1.x, FIELD_W)
                        d_y = wrap_delta(projectile.y, ship1.y, FIELD_H)
                        if math.hypot(d_x, d_y) < (projectile.radius + ship1.radius):
                            ship1.take_damage(projectile.damage)
                            projectile.active = False
                # Столкновение с астероидами
                for asteroid in asteroids:
                    d_x = wrap_delta(projectile.x, asteroid.x, FIELD_W)
                    d_y = wrap_delta(projectile.y, asteroid.y, FIELD_H)
                    if math.hypot(d_x, d_y) < (projectile.radius + asteroid.radius):
                        asteroid.active = False
                        projectile.active = False
                        break
                # Столкновение с планетой (поглощение)
                d_x = wrap_delta(projectile.x, planet.x, FIELD_W)
                d_y = wrap_delta(projectile.y, planet.y, FIELD_H)
                if math.hypot(d_x, d_y) < (projectile.radius + planet.radius):
                    projectile.active = False

        missiles = [m for m in missiles if m.active]
        asteroids = [a for a in asteroids if a.active]

        from project.collisions import (handle_planet_collision, handle_ship_asteroid_collision,
                                        handle_ship_ship_collision, handle_asteroid_collision)
        handle_planet_collision(ship1, planet)
        handle_planet_collision(ship2, planet)
        for asteroid in asteroids:
            handle_ship_asteroid_collision(ship1, asteroid)
            handle_ship_asteroid_collision(ship2, asteroid)
        handle_ship_ship_collision(ship1, ship2)
        for i in range(len(asteroids)):
            for j in range(i + 1, len(asteroids)):
                handle_asteroid_collision(asteroids[i], asteroids[j])
        for i, asteroid in enumerate(asteroids):
            d_x = wrap_delta(asteroid.x, planet.x, FIELD_W)
            d_y = wrap_delta(asteroid.y, planet.y, FIELD_H)
            if math.hypot(d_x, d_y) < (planet.radius + asteroid.radius):
                asteroids[i] = generate_offscreen_asteroid(cam, GAME_SCREEN_W / MIN_VISIBLE_WIDTH)

        cam.update_center_on_two_ships(ship1, ship2)
        dx_cam = cam.x - prevCamX
        dy_cam = cam.y - prevCamY
        if dx_cam > FIELD_W / 2:
            dx_cam -= FIELD_W
        elif dx_cam < -FIELD_W / 2:
            dx_cam += FIELD_W
        if dy_cam > FIELD_H / 2:
            dy_cam -= FIELD_H
        elif dy_cam < -FIELD_H / 2:
            dy_cam += FIELD_H
        globalCamX += dx_cam
        globalCamY += dy_cam
        prevCamX = cam.x
        prevCamY = cam.y

        d_x_ship = wrap_delta(ship1.x, ship2.x, FIELD_W)
        d_y_ship = wrap_delta(ship1.y, ship2.y, FIELD_H)
        ship_distance = math.hypot(d_x_ship, d_y_ship)
        desired_visible_width = max(ship_distance * MARGIN, MIN_VISIBLE_WIDTH)
        desired_visible_width = min(desired_visible_width, GAME_SCREEN_W)
        zoom = GAME_SCREEN_W / desired_visible_width

        screen.fill((0, 0, 40))
        draw_star_layer_colored(screen, star_layer_far, globalCamX, globalCamY, 0.3, zoom)
        draw_star_layer_colored(screen, star_layer_mid, globalCamX, globalCamY, 0.6, zoom)
        draw_star_layer_colored(screen, star_layer_near, globalCamX, globalCamY, 1.0, zoom)

        px, py = world_to_screen(planet.x, planet.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, planet.color, (px, py), int(planet.radius * zoom))

        for asteroid in asteroids:
            asteroid.draw(screen, cam, zoom)
        for projectile in missiles:
            projectile.draw(screen, cam, zoom)

        for ship in (ship1, ship2):
            sx, sy = world_to_screen(ship.x, ship.y, cam.x, cam.y, zoom)
            r = int(ship.radius * zoom)
            pygame.draw.circle(screen, ship.color, (sx, sy), r)
            tip_x = sx + int(r * math.sin(math.radians(ship.angle)))
            tip_y = sy - int(r * math.cos(math.radians(ship.angle)))
            pygame.draw.line(screen, (0, 0, 0), (sx, sy), (tip_x, tip_y), 2)
            for (tx, ty, t) in ship.active_lasers:
                angle = math.atan2(ty - ship.y, tx - ship.x)
                start_x = ship.x + ship.radius * math.cos(angle)
                start_y = ship.y + ship.radius * math.sin(angle)
                start = world_to_screen(start_x, start_y, cam.x, cam.y, zoom)
                end = world_to_screen(tx, ty, cam.x, cam.y, zoom)
                pygame.draw.line(screen, (0, 255, 0), start, end, 2)

        panel_rect = pygame.Rect(GAME_SCREEN_W, 0, PANEL_WIDTH, SCREEN_H)
        pygame.draw.rect(screen, (50, 50, 50), panel_rect)

        x_panel = GAME_SCREEN_W + 10
        y_panel = 10
        font_panel = pygame.font.SysFont("Arial", 18)

        text = font_panel.render(ship1.name, True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Crew: {ship1.crew}/{ship1.max_crew}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Energy: {ship1.energy}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize() * 2

        text = font_panel.render(ship2.name, True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Crew: {ship2.crew}/{ship2.max_crew}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += font_panel.get_linesize()
        text = font_panel.render(f"Energy: {ship2.energy}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
