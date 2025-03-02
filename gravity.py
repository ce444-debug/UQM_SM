import math
from config import GRAVITY_RANGE, GRAVITY_STRENGTH, FIELD_W, FIELD_H
from utils import wrap_delta, wrap_position

def apply_gravity(ship, planet, dt):
    dx = wrap_delta(ship.x, planet.x, FIELD_W)
    dy = wrap_delta(ship.y, planet.y, FIELD_H)
    distance = math.hypot(dx, dy)
    if distance < GRAVITY_RANGE and distance != 0:
        factor = (1 - distance / GRAVITY_RANGE)
        accel = GRAVITY_STRENGTH * factor * 1.5
        nx = dx / distance
        ny = dy / distance
        ship.vx += nx * accel * dt
        ship.vy += ny * accel * dt
