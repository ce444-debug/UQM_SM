from project.model.utils import wrap_position
import pygame

class Projectile:
    def __init__(self, x, y, vx, vy, damage, radius):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = damage
        self.radius = radius
        self.active = True

    def update(self, dt):
        # Базовая логика обновления: простое движение с учетом инерции
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap_position(self.x, self.y)

    def draw(self, screen, cam, zoom, color=(255, 255, 255)):
        from project.model.utils import world_to_screen
        sx, sy = world_to_screen(self.x, self.y, cam.x, cam.y, zoom)
        pygame.draw.circle(screen, color, (sx, sy), int(self.radius * zoom))

    def on_hit(self, target):
        # При попадании наносим урон цели и деактивируем снаряд
        target.take_damage(self.damage)
        self.active = False
