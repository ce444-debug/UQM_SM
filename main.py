import pygame
import sys
import math
import random

from config import *
from utils import spawn_ship, wrap_delta
from gravity import apply_gravity
from collisions import (handle_planet_collision, handle_ship_asteroid_collision,
                        handle_ship_ship_collision, handle_asteroid_collision)
from stars import generate_colored_stars, draw_star_layer_colored
from project.entities.planet import Planet
from project.entities.asteroid import Asteroid
from project.entities.camera import Camera
from project.ships.ship_a import ShipA
from project.ships.ship_b import ShipB

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Combat Zone with Gravity-Boosted Ships")

def generate_offscreen_asteroid(cam, zoom):
    margin = 20
    while True:
        x = random.uniform(0, FIELD_W)
        y = random.uniform(0, FIELD_H)
        sx, sy =  __import__("utils").world_to_screen(x, y, cam.x, cam.y, zoom)
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
    clock = pygame.time.Clock()
    game_time = 0

    font = pygame.font.SysFont("Arial", 18)
    line_height = font.get_linesize()

    star_layer_far  = generate_colored_stars(180)
    star_layer_mid  = generate_colored_stars(120)
    star_layer_near = generate_colored_stars(80)

    sx1, sy1 = spawn_ship()
    sx2, sy2 = spawn_ship()
    shipA = ShipA(sx1, sy1, (255, 100, 100))
    shipB = ShipB(sx2, sy2, (100, 200, 255))

    planet = Planet(FIELD_W / 2, FIELD_H / 2, 30, (180, 180, 180))
    cam = Camera(FIELD_W / 2, FIELD_H / 2)
    globalCamX = cam.x
    globalCamY = cam.y
    prevCamX = cam.x
    prevCamY = cam.y

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

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        game_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break

        keys = pygame.key.get_pressed()

        # Управление поворотом и ускорением кораблей
        if keys[pygame.K_LEFT]:
            shipA.angle = (shipA.angle - shipA.turn_speed * dt) % 360
        if keys[pygame.K_RIGHT]:
            shipA.angle = (shipA.angle + shipA.turn_speed * dt) % 360
        if keys[pygame.K_UP]:
            rad = math.radians(shipA.angle)
            a = shipA.thrust_increment / shipA.thrust_wait
            shipA.vx += a * dt * math.sin(rad)
            shipA.vy -= a * dt * math.cos(rad)
            current_speed = math.hypot(shipA.vx, shipA.vy)
            if current_speed > shipA.max_thrust:
                factor = shipA.max_thrust / current_speed
                shipA.vx *= factor
                shipA.vy *= factor

        if keys[pygame.K_s]:
            shipB.angle = (shipB.angle - shipB.turn_speed * dt) % 360
        if keys[pygame.K_f]:
            shipB.angle = (shipB.angle + shipB.turn_speed * dt) % 360
        if keys[pygame.K_e]:
            rad = math.radians(shipB.angle)
            a = shipB.thrust_increment / shipB.thrust_wait
            shipB.vx += a * dt * math.sin(rad)
            shipB.vy -= a * dt * math.cos(rad)
            current_speed = math.hypot(shipB.vx, shipB.vy)
            if current_speed > shipB.max_thrust:
                factor = shipB.max_thrust / current_speed
                shipB.vx *= factor
                shipB.vy *= factor

        # Применяем демпфирование и гравитацию
        shipA.vx *= 0.997
        shipA.vy *= 0.997
        shipB.vx *= 0.997
        shipB.vy *= 0.997

        from gravity import apply_gravity
        apply_gravity(shipA, planet, dt)
        apply_gravity(shipB, planet, dt)

        # Обработка оружия
        if keys[pygame.K_RCTRL]:
            missile = shipA.fire_missile(shipB, game_time)
            if missile:
                missiles.append(missile)
        if keys[pygame.K_RSHIFT]:
            shipA.fire_laser_defense([shipB] + asteroids + missiles, game_time)
        if keys[pygame.K_a]:
            missile = shipB.fire_missile(shipA, game_time)
            if missile:
                missiles.append(missile)
        if keys[pygame.K_q]:
            shipB.fire_laser_defense([shipA] + asteroids + missiles, game_time)

        shipA.update(dt)
        shipB.update(dt)
        for asteroid in asteroids:
            asteroid.update(dt)
        for missile in missiles:
            missile.update(dt)
            if missile.active:
                d_x = wrap_delta(missile.x, missile.target.x, FIELD_W)
                d_y = wrap_delta(missile.y, missile.target.y, FIELD_H)
                if math.hypot(d_x, d_y) < (missile.radius + missile.target.radius):
                    missile.target.take_damage(missile.damage)
                    missile.active = False
        missiles = [m for m in missiles if m.active]
        asteroids = [a for a in asteroids if a.active]

        from collisions import (handle_planet_collision, handle_ship_asteroid_collision,
                                  handle_ship_ship_collision, handle_asteroid_collision)
        handle_planet_collision(shipA, planet)
        handle_planet_collision(shipB, planet)
        for asteroid in asteroids:
            handle_ship_asteroid_collision(shipA, asteroid)
            handle_ship_asteroid_collision(shipB, asteroid)
        handle_ship_ship_collision(shipA, shipB)
        for i in range(len(asteroids)):
            for j in range(i + 1, len(asteroids)):
                handle_asteroid_collision(asteroids[i], asteroids[j])
        for i, asteroid in enumerate(asteroids):
            d_x = wrap_delta(asteroid.x, planet.x, FIELD_W)
            d_y = wrap_delta(asteroid.y, planet.y, FIELD_H)
            if math.hypot(d_x, d_y) < (planet.radius + asteroid.radius):
                asteroids[i] = generate_offscreen_asteroid(cam, GAME_SCREEN_W / MIN_VISIBLE_WIDTH)

        cam.update_center_on_two_ships(shipA, shipB)
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

        d_x_ship = wrap_delta(shipA.x, shipB.x, FIELD_W)
        d_y_ship = wrap_delta(shipA.y, shipB.y, FIELD_H)
        ship_distance = math.hypot(d_x_ship, d_y_ship)
        desired_visible_width = max(ship_distance * MARGIN, MIN_VISIBLE_WIDTH)
        desired_visible_width = min(desired_visible_width, GAME_SCREEN_W)
        zoom = GAME_SCREEN_W / desired_visible_width

        game_area = pygame.Rect(0, 0, GAME_SCREEN_W, SCREEN_H)
        pygame.draw.rect(screen, (0, 0, 40), game_area)
        draw_star_layer_colored(screen, star_layer_far, globalCamX, globalCamY, 0.3, zoom)
        draw_star_layer_colored(screen, star_layer_mid, globalCamX, globalCamY, 0.6, zoom)
        draw_star_layer_colored(screen, star_layer_near, globalCamX, globalCamY, 1.0, zoom)
        from utils import world_to_screen
        px, py = world_to_screen(planet.x, planet.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, planet.color, (px, py), int(planet.radius * zoom))
        for asteroid in asteroids:
            asteroid.draw(screen, cam, zoom)
        for missile in missiles:
            missile.draw(screen, cam, zoom)
        for ship in (shipA, shipB):
            sx, sy = world_to_screen(ship.x, ship.y, cam.x, cam.y, zoom)
            r = int(ship.radius * zoom)
            pygame.draw.circle(screen, ship.color, (sx, sy), r)
            tip_x = sx + int(r * math.sin(math.radians(ship.angle)))
            tip_y = sy - int(r * math.cos(math.radians(ship.angle)))
            pygame.draw.line(screen, (0, 0, 0), (sx, sy), (tip_x, tip_y), 2)
            if ship.spawn_timer > 0:
                effect_radius = int(r * (1 + 0.5 * ship.spawn_timer))
                pygame.draw.circle(screen, (255, 255, 0), (sx, sy), effect_radius, 2)
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
        text = font.render(shipA.name, True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += line_height
        text = font.render(f"Crew: {shipA.crew}/{shipA.max_crew}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += line_height
        text = font.render(f"Energy: {shipA.energy}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += line_height * 2
        text = font.render(shipB.name, True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += line_height
        text = font.render(f"Crew: {shipB.crew}/{shipB.max_crew}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))
        y_panel += line_height
        text = font.render(f"Energy: {shipB.energy}", True, (255, 255, 255))
        screen.blit(text, (x_panel, y_panel))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
