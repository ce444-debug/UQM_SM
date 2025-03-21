import math
from project.config import FIELD_W, FIELD_H
from project.utils import wrap_delta  # Теперь используем wrap_delta для вычисления разницы

def handle_planet_collision(ship, planet, game_time):
    """
    Обрабатывает столкновение корабля с планетой.
    Если расстояние между центрами корабля и планеты меньше суммы их радиусов,
    корабль корректируется (сдвигается так, чтобы выйти за пределы планеты) и его скорость отражается.
    При этом, если прошло более 0.5 секунд с предыдущего столкновения с планетой,
    кораблю наносится 1 единица урона экипажа.
    """
    dx = wrap_delta(planet.x, ship.x, FIELD_W)
    dy = wrap_delta(planet.y, ship.y, FIELD_H)
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

        impulse = ship.thrust_increment * 8
        ship.vx += impulse * nx
        ship.vy += impulse * ny

        if not hasattr(ship, "last_planet_collision"):
            ship.last_planet_collision = 0
        if game_time - ship.last_planet_collision > 0.5:
            ship.take_damage(1)
            ship.last_planet_collision = game_time

def handle_ship_asteroid_collision(ship, asteroid):
    # Оптимизация: Проверяем столкновение, только если объекты близко
    collision_margin = 100
    if abs(ship.x - asteroid.x) > collision_margin or abs(ship.y - asteroid.y) > collision_margin:
        return

    dx = wrap_delta(asteroid.x, ship.x, FIELD_W)
    dy = wrap_delta(asteroid.y, ship.y, FIELD_H)
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
    dx = wrap_delta(ship2.x, ship1.x, FIELD_W)
    dy = wrap_delta(ship2.y, ship1.y, FIELD_H)
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

def handle_asteroid_collision(asteroid1, asteroid2):
    dx = wrap_delta(asteroid2.x, asteroid1.x, FIELD_W)
    dy = wrap_delta(asteroid2.y, asteroid1.y, FIELD_H)
    dist = math.hypot(dx, dy)
    min_dist = asteroid1.radius + asteroid2.radius
    if dist < min_dist:
        if dist == 0:
            nx, ny = 1.0, 0.0
        else:
            nx = dx / dist
            ny = dy / dist
        overlap = min_dist - dist
        asteroid1.x += nx * (overlap / 2)
        asteroid1.y += ny * (overlap / 2)
        asteroid2.x -= nx * (overlap / 2)
        asteroid2.y -= ny * (overlap / 2)
        dvx = asteroid1.vx - asteroid2.vx
        dvy = asteroid1.vy - asteroid2.vy
        p = dvx * nx + dvy * ny
        asteroid1.vx -= p * nx
        asteroid1.vy -= p * ny
        asteroid2.vx += p * nx
        asteroid2.vy += p * ny
