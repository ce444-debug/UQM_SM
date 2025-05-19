import pygame
import sys
from menu import SuperMeleeMenu
from game import Game
from project.config import SCREEN_W, SCREEN_H

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    menu = SuperMeleeMenu(screen, clock)
    state = "MENU"

    while True:
        if state == "MENU":
            config = menu.display()
            game = Game(config, menu)
            state = game.run()
        else:
            menu.save_last_config()
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()