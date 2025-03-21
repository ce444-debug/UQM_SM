import math
import pygame
from project.utils import wrap_delta, world_to_screen

class World:
    def __init__(self, initial_time=0):
        self.entities = []  # Список всех динамических объектов (корабли, астероиды, снаряды)
        self.game_time = initial_time

    def add(self, entity):
        if entity not in self.entities:
            self.entities.append(entity)

    def remove(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)

    def update(self, dt):
        self.game_time += dt
        for entity in self.entities:
            if hasattr(entity, "update"):
                try:
                    from project.entities.mine import Plasmoid
                    if isinstance(entity, Plasmoid):
                        entity.update(dt, self.game_time)
                    else:
                        entity.update(dt)
                except Exception:
                    entity.update(dt)

    def draw(self, screen, cam, zoom):
        from project.ships.base_ship import BaseShip
        for entity in self.entities:
            if isinstance(entity, BaseShip):
                # Отрисовка корабля согласно исходной логике
                sx, sy = world_to_screen(entity.x, entity.y, cam.x, cam.y, zoom)
                r = int(entity.radius * zoom)
                pygame.draw.circle(screen, entity.color, (sx, sy), r)
                tip_x = sx + int(r * math.sin(math.radians(entity.angle)))
                tip_y = sy - int(r * math.cos(math.radians(entity.angle)))
                pygame.draw.line(screen, (0, 0, 0), (sx, sy), (tip_x, tip_y), 2)
                for (tx, ty, t) in entity.active_lasers:
                    angle = math.atan2(ty - entity.y, tx - entity.x)
                    start_x = entity.x + entity.radius * math.cos(angle)
                    start_y = entity.y + entity.radius * math.sin(angle)
                    start = world_to_screen(start_x, start_y, cam.x, cam.y, zoom)
                    end = world_to_screen(tx, ty, cam.x, cam.y, zoom)
                    pygame.draw.line(screen, (0, 255, 0), start, end, 2)
            elif hasattr(entity, "draw"):
                entity.draw(screen, cam, zoom)

    def filter_entities(self, condition):
        return [e for e in self.entities if condition(e)]

    def cleanup(self):
        self.entities = [e for e in self.entities if getattr(e, "active", True)]
