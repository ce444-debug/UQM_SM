import pygame
from menu import SuperMeleeMenu
from game import Game
from project.config import SCREEN_W, SCREEN_H


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    running = True
    while running:
        # Создаем и ждем меню
        menu = SuperMeleeMenu(screen, clock)
        config = menu.display()  # Ожидание выбора
        if config is None:
            running = False
            break
        print("Loaded config:", config)

        # Запускаем игру
        game = Game(config)
        game.run()  # Важно: внутри game.run() не должно быть pygame.quit()

        # Переинициализируем дисплей и шрифты
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

        # Очистка очереди событий и небольшая задержка для сброса системы
        pygame.event.clear()
        pygame.time.wait(50)

        # После этого цикл повторяется – меню должно сразу быть готовым
    pygame.quit()


if __name__ == "__main__":
    main()
