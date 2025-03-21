from game import Game
from menu import MainMenu, ModeMenu, DifficultyMenu
import pygame
from project.config import SCREEN_W, SCREEN_H

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
        # Пока настройки перенаправляют на игру
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

    game = Game(game_mode=mode_option, difficulty=difficulty)
    game.run()

if __name__ == "__main__":
    main()
