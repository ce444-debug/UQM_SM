import math
from config import FIELD_W, FIELD_H
from utils import wrap_delta, wrap_position

def handle_planet_collision(ship, planet):
    dx = ship.x - planet.x
    dy = ship.y - planet.y
    dist = math.hypot(dx, dy)
    min_dist = ship.radius + planet.radius
    if dist < min_dist:
        if dist == 0:
            nx, ny = 1.0, 0.0
        else:
            nx = dx / dist
            ny = dy / dist
        overlap = min_dist - dist
        ship.x += nx * overlap
        ship.y += ny * overlap
        dot = ship.vx * nx + ship.vy * ny
        ship.vx -= 2.0 * dot * nx
        ship.vy -= 2.0 * dot * ny

def handle_ship_asteroid_collision(ship, asteroid):
    dx = ship.x - asteroid.x
    dy = ship.y - asteroid.y
    dist = math.hypot(dx, dy)
    min_dist = ship.radius + asteroid.radius
    if dist < min_dist:
        if dist == 0:
            nx, ny = 1.0, 0.0
        else:
            nx = dx / dist
            ny = dy / dist
        overlap = min_dist - dist
        ship.x += nx * (overlap / 2)
        ship.y += ny * (overlap / 2)
        asteroid.x -= nx * (overlap / 2)
        asteroid.y -= ny * (overlap / 2)
        dvx = ship.vx - asteroid.vx
        dvy = ship.vy - asteroid.vy
        p = dvx * nx + dvy * ny
        ship.vx -= p * nx
        ship.vy -= p * ny
        asteroid.vx += p * nx
        asteroid.vy += p * ny

def handle_ship_ship_collision(ship1, ship2):
    dx = ship1.x - ship2.x
    dy = ship1.y - ship2.y
    dist = math.hypot(dx, dy)
    min_dist = ship1.radius + ship2.radius
    if dist < min_dist:
        if dist == 0:
            nx, ny = 1.0, 0.0
        else:
            nx = dx / dist
            ny = dy / dist
        overlap = min_dist - dist
        ship1.x += nx * (overlap / 2)
        ship1.y += ny * (overlap / 2)
        ship2.x -= nx * (overlap / 2)
        ship2.y -= ny * (overlap / 2)
        dvx = ship1.vx - ship2.vx
        dvy = ship1.vy - ship2.vy
        p = dvx * nx + dvy * ny
        ship1.vx -= p * nx
        ship1.vy -= p * ny
        ship2.vx += p * nx
        ship2.vy += p * ny

def handle_asteroid_collision(ast1, ast2):
    dx = ast1.x - ast2.x
    dy = ast1.y - ast2.y
    dist = math.hypot(dx, dy)
    min_dist = ast1.radius + ast2.radius
    if dist < min_dist:
        if dist == 0:
            nx, ny = 1.0, 0.0
        else:
            nx = dx / dist
            ny = dy / dist
        overlap = min_dist - dist
        ast1.x += nx * (overlap / 2)
        ast1.y += ny * (overlap / 2)
        ast2.x -= nx * (overlap / 2)
        ast2.y -= ny * (overlap / 2)
        dvx = ast1.vx - ast2.vx
        dvy = ast1.vy - ast2.vy
        p = dvx * nx + dvy * ny
        ast1.vx -= p * nx
        ast1.vy -= p * ny
        ast2.vx += p * nx
        ast2.vy += p * ny
