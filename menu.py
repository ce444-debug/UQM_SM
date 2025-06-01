import pygame
import sys
import json
import random
from project.ships.registry import SHIP_CLASSES
from project.config import SCREEN_W, SCREEN_H, PANEL_WIDTH, GAME_SCREEN_W

# Цвета
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)

SAVES_FILE = "saved_teams.json"

CONTROL_OPTIONS = ["Human Control", "Weak Cyborg", "Good Cyborg", "Awesome Cyborg"]

LEFT_PANEL_COLS = 7

# CACHING ADDED: глобальная переменная для кэширования загруженной конфигурации
_CACHED_CONFIG = None

class SuperMeleeMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock

        self.font_title = pygame.font.SysFont("Arial", 48)
        self.font_menu = pygame.font.SysFont("Arial", 36)
        self.font_small = pygame.font.SysFont("Arial", 20)

        self.state = "main_menu"

        # 14 слотов флота
        self.team_slots = 14
        self.teams = {"Team 1": [None] * self.team_slots,
                      "Team 2": [None] * self.team_slots}
        self.team_names = {"Team 1": "Team 1",
                           "Team 2": "Team 2"}

        self.settings = {
            "Team 1": {"control": "Human Control"},
            "Team 2": {"control": "Good Cyborg"}
        }

        # Изменено: по умолчанию фокус главного меню на правой панели (selected_right = 0)
        self.selected_right = 0
        # Фокус левой панели: -1 означает, что курсор на заголовке (Team Name),
        # 0..(team_slots-1) – выбранная ячейка флота.
        self.selected_slot = -1
        self.selected_team = "Team 1"
        self.last_upper_slot = 0

        # Правые опции: первые три для Team 1, затем Battle, потом Save/Load для Team 2, затем Control для Team 2 и Quit.
        self.right_options = [
            ("Team 1", "control"),
            ("Team 1", "save"),
            ("Team 1", "load"),
            ("Battle", None),
            ("Team 2", "save"),
            ("Team 2", "load"),
            ("Team 2", "control"),
            ("Quit", "quit")
        ]

        self.ship_list = list(SHIP_CLASSES.keys()) + ["?"]
        self.selected_ship_index = 0
        self.editing_team_name = ""
        self.editing_team = False  # Режим редактирования имени включается при клике по заголовку
        self.initial_ships = {"Team 1": None, "Team 2": None}

        self.confirm_team1 = False
        self.confirm_team2 = False

        # CACHING ADDED: Используем глобальный кэш конфигурации, чтобы минимизировать чтение файла
        global _CACHED_CONFIG
        if _CACHED_CONFIG is not None:
            # Если конфигурация уже загружена ранее – используем её
            self.last_config = _CACHED_CONFIG
            self.teams = _CACHED_CONFIG.get("teams", self.teams)
            self.team_names = _CACHED_CONFIG.get("team_names", self.team_names)
            self.settings = _CACHED_CONFIG.get("settings", self.settings)
        else:
            try:
                with open(SAVES_FILE, "r") as f:
                    saves = json.load(f)
                if saves and "last_config" in saves:
                    config = saves["last_config"]
                    self.teams = config.get("teams", self.teams)
                    self.team_names = config.get("team_names", self.team_names)
                    self.settings = config.get("settings", self.settings)
                    if "mode" not in config:
                        config["mode"] = f"{self.settings['Team 1']['control']} vs {self.settings['Team 2']['control']}"
                    self.last_config = config
                    _CACHED_CONFIG = config  # Сохраняем в кэш
            except Exception as e:
                pass

        self.normalize_teams()

    def normalize_teams(self):
        for team in self.teams:
            while len(self.teams[team]) < self.team_slots:
                self.teams[team].append(None)
            if len(self.teams[team]) > self.team_slots:
                self.teams[team] = self.teams[team][:self.team_slots]

    def get_opposite_slot(self, slot):
        if slot < 0:
            return 0
        if slot < LEFT_PANEL_COLS:
            return slot + LEFT_PANEL_COLS
        else:
            return slot - LEFT_PANEL_COLS

    def draw_main_menu(self):
        self.screen.fill(BLACK)
        left_rect = pygame.Rect(0, 0, GAME_SCREEN_W, SCREEN_H)
        pygame.draw.rect(self.screen, (30, 30, 30), left_rect)
        title_surface = self.font_title.render("Super melee", True, YELLOW)
        self.screen.blit(title_surface, (20, 10))
        team1_area = pygame.Rect(10, 80, GAME_SCREEN_W - 20, (SCREEN_H - 100) // 2 - 10)
        team2_area = pygame.Rect(10, team1_area.bottom + 20, GAME_SCREEN_W - 20, (SCREEN_H - 100) // 2 - 10)
        pygame.draw.rect(self.screen, (50,50,50), team1_area, 2)
        pygame.draw.rect(self.screen, (50,50,50), team2_area, 2)
        self.draw_team_panel("Team 1", team1_area)
        self.draw_team_panel("Team 2", team2_area)
        right_rect = pygame.Rect(GAME_SCREEN_W, 0, PANEL_WIDTH, SCREEN_H)
        pygame.draw.rect(self.screen, (40,40,40), right_rect)
        self.draw_right_panel(right_rect)

    def draw_team_panel(self, team, area):
        name = self.team_names.get(team, team)
        if self.selected_right == -1 and self.selected_team == team and self.selected_slot == -1 and self.editing_team:
            edit_text = self.font_menu.render(self.editing_team_name, True, YELLOW)
            self.screen.blit(edit_text, (area.x + 10, area.y + 10))
        else:
            name_surface = self.font_menu.render(name, True, WHITE)
            self.screen.blit(name_surface, (area.x + 10, area.y + 10))
            if self.selected_right == -1 and self.selected_team == team and self.selected_slot == -1:
                pygame.draw.rect(self.screen, YELLOW, (area.x + 8, area.y + 8,
                                                       name_surface.get_width() + 4,
                                                       name_surface.get_height() + 4), 1)
        slot_margin = 5
        cols = LEFT_PANEL_COLS
        slot_width = (area.width - 20 - (cols - 1) * slot_margin) // cols
        slot_height = 40
        start_y = area.y + 60
        points = 0
        for idx in range(self.team_slots):
            row = idx // cols
            col = idx % cols
            slot_x = area.x + 10 + col * (slot_width + slot_margin)
            slot_y = start_y + row * (slot_height + slot_margin)
            slot_rect = pygame.Rect(slot_x, slot_y, slot_width, slot_height)
            pygame.draw.rect(self.screen, GRAY, slot_rect, 1)
            ship_name = self.teams[team][idx] if self.teams[team][idx] is not None else "---"
            if self.selected_right == -1 and self.selected_team == team and self.selected_slot == idx:
                pygame.draw.rect(self.screen, YELLOW, slot_rect, 2)
            slot_text = self.font_small.render(ship_name, True, WHITE)
            self.screen.blit(slot_text, (slot_rect.x + 5, slot_rect.y + 10))
            if ship_name != "---" and ship_name in SHIP_CLASSES:
                try:
                    dummy = SHIP_CLASSES[ship_name](0, 0, WHITE)
                    points += getattr(dummy, "cost", 0)
                except:
                    pass
        points_text = self.font_small.render(f"Points: {points}", True, WHITE)
        self.screen.blit(points_text, (area.x + 10, area.bottom - 30))

    def draw_right_panel(self, area):
        current_y = 20
        for idx, (team_option, action) in enumerate(self.right_options):
            if team_option == "Battle":
                option_height = 80
            elif action == "control":
                option_height = 60
            else:
                option_height = 40
            if action == "quit":
                current_y += 20
            rect = pygame.Rect(area.x + 10, current_y, area.width - 20, option_height)
            if self.selected_right == idx:
                pygame.draw.rect(self.screen, YELLOW, rect, 2)
            else:
                pygame.draw.rect(self.screen, GRAY, rect, 1)
            if team_option == "Battle":
                if self.selected_right == -1:
                    if self.selected_slot == -1:
                        battle_text = "Team name"
                    else:
                        ship_name = self.teams[self.selected_team][self.selected_slot]
                        if ship_name and ship_name in SHIP_CLASSES:
                            dummy = SHIP_CLASSES[ship_name](0, 0, WHITE)
                            battle_text = (f"{dummy.name} C:{dummy.crew}/{dummy.max_crew} "
                                           f"E:{dummy.energy}/{dummy.max_energy} ${dummy.cost}")
                        else:
                            battle_text = "Empty slot"
                else:
                    battle_text = "Battle!"
            elif action == "control":
                battle_text = f"{self.settings[team_option]['control']}"
            elif action == "save":
                battle_text = "Save"
            elif action == "load":
                battle_text = "Load"
            elif action == "quit":
                battle_text = "Quit"
            else:
                battle_text = ""
            if team_option == "Battle" or action == "quit":
                txt_surf = self.font_small.render(battle_text, True, WHITE)
            elif action == "control":
                txt_surf = self.font_menu.render(battle_text, True, WHITE)
            else:
                txt_surf = self.font_small.render(battle_text, True, WHITE)
            self.screen.blit(txt_surf, (rect.x + 5, rect.y + (option_height - txt_surf.get_height()) // 2))
            current_y += option_height + 10

    def draw_ship_select(self):
        self.screen.fill((20, 20, 60))
        title = self.font_title.render("Select Ship", True, YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 20))
        info = self.font_small.render("Use arrows, Enter to select, Esc to cancel", True, WHITE)
        self.screen.blit(info, (50, SCREEN_H - 40))
        list_x = SCREEN_W // 2 - 100
        list_y = 100
        for i, ship in enumerate(self.ship_list):
            color = YELLOW if i == self.selected_ship_index else GRAY
            ship_text = self.font_menu.render(ship, True, color)
            self.screen.blit(ship_text, (list_x, list_y + i * 40))

    def draw_team_name_edit(self):
        pass

    # Изменено: Новый метод draw_battle_select – отрисовка таблиц выбора стартовых кораблей без заголовков и рамок
    def draw_battle_select(self, sel1, sel2, active_team):
        self.screen.fill(BLACK)
        panel1 = pygame.Rect(10, 80, GAME_SCREEN_W - 20, (SCREEN_H - 100) // 2)
        panel2 = pygame.Rect(10, panel1.bottom + 20, GAME_SCREEN_W - 20, (SCREEN_H - 100) // 2)
        total_cells = self.team_slots + 2  # 16 ячеек: индексы 0..(team_slots-1) – реальные слоты, team_slots -> "?" и team_slots+1 -> "X"
        cols = 4
        cell_margin = 5
        cell_width = (panel1.width - 20 - (cols - 1) * cell_margin) // cols
        cell_height = 40
        # Таблица для Team 1
        for idx in range(total_cells):
            r = idx // cols
            c = idx % cols
            x = panel1.x + 10 + c * (cell_width + cell_margin)
            y = panel1.y + 10 + r * (cell_height + cell_margin)
            cell_rect = pygame.Rect(x, y, cell_width, cell_height)
            if idx == sel1:
                pygame.draw.rect(self.screen, YELLOW, cell_rect, 2)
            else:
                pygame.draw.rect(self.screen, GRAY, cell_rect, 1)
            if idx < self.team_slots:
                text = self.teams["Team 1"][idx] if self.teams["Team 1"][idx] is not None else "---"
            elif idx == self.team_slots:
                text = "?"
            else:
                text = "X"
            txt_surf = self.font_small.render(str(text), True, WHITE)
            self.screen.blit(txt_surf, (cell_rect.x + 5, cell_rect.y + 10))
        # Таблица для Team 2
        for idx in range(total_cells):
            r = idx // cols
            c = idx % cols
            x = panel2.x + 10 + c * (cell_width + cell_margin)
            y = panel2.y + 10 + r * (cell_height + cell_margin)
            cell_rect = pygame.Rect(x, y, cell_width, cell_height)
            if idx == sel2:
                pygame.draw.rect(self.screen, YELLOW, cell_rect, 2)
            else:
                pygame.draw.rect(self.screen, GRAY, cell_rect, 1)
            if idx < self.team_slots:
                text = self.teams["Team 2"][idx] if self.teams["Team 2"][idx] is not None else "---"
            elif idx == self.team_slots:
                text = "?"
            else:
                text = "X"
            txt_surf = self.font_small.render(str(text), True, WHITE)
            self.screen.blit(txt_surf, (cell_rect.x + 5, cell_rect.y + 10))
        if active_team == "Team 1":
            instr = "Team1: Use E(up), D(down), S(left), F(right), A(confirm)"
        else:
            instr = "Team2: Use Arrow keys, RCTRL(confirm)"
        instr_surf = self.font_small.render(instr, True, WHITE)
        self.screen.blit(instr_surf, (10, SCREEN_H - 30))

    def battle_select_mode(self):
        # Для каждой команды – выбор индекса от 0 до team_slots+1
        battle_sel = {"Team 1": 0, "Team 2": 0}
        active_team = "Team 1"
        confirmed = {"Team 1": False, "Team 2": False}
        max_index = self.team_slots + 1  # Дополнительные 2 ячейки

        # Если контроль не Human, выбираем автоматически "?"
        if self.settings["Team 1"]["control"] != "Human Control":
            battle_sel["Team 1"] = self.team_slots
            confirmed["Team 1"] = True
        if self.settings["Team 2"]["control"] != "Human Control":
            battle_sel["Team 2"] = self.team_slots
            confirmed["Team 2"] = True

        while not (confirmed["Team 1"] and confirmed["Team 2"]):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    # Для Team 1 – используем клавиши: E=up, D=down, S=left, F=right, A=confirm
                    if active_team == "Team 1" and self.settings["Team 1"]["control"] == "Human Control":
                        if event.key == pygame.K_e:
                            if battle_sel["Team 1"] - 4 >= 0:
                                battle_sel["Team 1"] -= 4
                        elif event.key == pygame.K_d:
                            if battle_sel["Team 1"] + 4 <= max_index:
                                battle_sel["Team 1"] += 4
                        elif event.key == pygame.K_s:
                            if battle_sel["Team 1"] > 0:
                                battle_sel["Team 1"] -= 1
                        elif event.key == pygame.K_f:
                            if battle_sel["Team 1"] < max_index:
                                battle_sel["Team 1"] += 1
                        elif event.key == pygame.K_a:
                            confirmed["Team 1"] = True
                    # Для Team 2 – используем стрелки и RCTRL
                    elif active_team == "Team 2" and self.settings["Team 2"]["control"] == "Human Control":
                        if event.key == pygame.K_LEFT:
                            if battle_sel["Team 2"] > 0:
                                battle_sel["Team 2"] -= 1
                        elif event.key == pygame.K_RIGHT:
                            if battle_sel["Team 2"] < max_index:
                                battle_sel["Team 2"] += 1
                        elif event.key == pygame.K_UP:
                            if battle_sel["Team 2"] - 4 >= 0:
                                battle_sel["Team 2"] -= 4
                        elif event.key == pygame.K_DOWN:
                            if battle_sel["Team 2"] + 4 <= max_index:
                                battle_sel["Team 2"] += 4
                        elif event.key == pygame.K_RCTRL:
                            confirmed["Team 2"] = True
                    if event.key == pygame.K_TAB:
                        active_team = "Team 2" if active_team == "Team 1" else "Team 1"
            self.draw_battle_select(battle_sel["Team 1"], battle_sel["Team 2"], active_team)
            pygame.display.flip()
            self.clock.tick(30)

        sel1 = battle_sel["Team 1"]
        sel2 = battle_sel["Team 2"]
        # Если выбран слот "X" (индекс team_slots+1) для любой команды,
        # сбрасываем меню и немедленно возвращаем конфигурацию главного меню
        if sel1 == self.team_slots + 1 or sel2 == self.team_slots + 1:
            self.reset()  # Сброс состояния меню
            return self.generate_config()  # Немедленная генерация конфигурации главного меню
        ship1 = self.teams["Team 1"][sel1] if (sel1 >= 0 and sel1 < self.team_slots) else ("?" if sel1 == self.team_slots else None)
        ship2 = self.teams["Team 2"][sel2] if (sel2 >= 0 and sel2 < self.team_slots) else ("?" if sel2 == self.team_slots else None)
        self.initial_ships["Team 1"] = ship1
        self.initial_ships["Team 2"] = ship2
        self.state = "exit"
        config = {
            "mode": f"{self.settings['Team 1']['control']} vs {self.settings['Team 2']['control']}",
            "teams": self.teams,
            "team_names": self.team_names,
            "settings": self.settings,
            "initial_ships": self.initial_ships
        }
        return config

    # Новый метод reset() – сброс состояния меню
    def reset(self):
        self.state = "main_menu"
        self.selected_right = 0
        self.selected_slot = -1
        self.selected_team = "Team 1"

    # Новый метод generate_config() – немедленная генерация конфигурации меню
    def generate_config(self):
        return {
            "mode": f"{self.settings['Team 1']['control']} vs {self.settings['Team 2']['control']}",
            "teams": self.teams,
            "team_names": self.team_names,
            "settings": self.settings,
            "initial_ships": self.initial_ships
        }

    def handle_main_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if self.editing_team:
                    if event.key == pygame.K_RETURN:
                        self.team_names[self.selected_team] = self.editing_team_name
                        self.editing_team = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.editing_team_name = self.editing_team_name[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.editing_team = False
                        self.editing_team_name = ""
                    else:
                        self.editing_team_name += event.unicode
                    return
                if self.selected_right == -1:
                    if event.key == pygame.K_UP:
                        if self.selected_slot == -1:
                            if self.selected_team == "Team 2":
                                self.selected_team = "Team 1"
                                self.selected_slot = self.get_opposite_slot(self.last_upper_slot)
                        else:
                            new_slot = self.selected_slot - LEFT_PANEL_COLS
                            if new_slot < -1:
                                self.selected_slot = -1
                            else:
                                self.selected_slot = new_slot
                    elif event.key == pygame.K_DOWN:
                        if self.selected_slot == -1:
                            self.selected_slot = 0
                        else:
                            new_slot = self.selected_slot + LEFT_PANEL_COLS
                            if new_slot >= self.team_slots:
                                if self.selected_team == "Team 1":
                                    self.last_upper_slot = self.selected_slot
                                    self.selected_team = "Team 2"
                                    self.selected_slot = -1
                                else:
                                    pass
                            else:
                                self.selected_slot = new_slot
                    elif event.key == pygame.K_LEFT:
                        if self.selected_slot == -1:
                            pass
                        else:
                            col = self.selected_slot % LEFT_PANEL_COLS
                            if col > 0:
                                self.selected_slot -= 1
                            else:
                                self.selected_slot = -1
                    elif event.key == pygame.K_RIGHT:
                        if self.selected_slot == -1:
                            self.selected_slot = 0
                        else:
                            col = self.selected_slot % LEFT_PANEL_COLS
                            if col < LEFT_PANEL_COLS - 1 and self.selected_slot < self.team_slots - 1:
                                self.selected_slot += 1
                            else:
                                self.selected_right = 3
                    elif event.key == pygame.K_RETURN:
                        if self.selected_slot == -1:
                            self.editing_team = True
                            self.editing_team_name = self.team_names[self.selected_team]
                        else:
                            self.state = "ship_select"
                            self.selected_ship_index = 0
                    elif event.key == pygame.K_TAB:
                        self.selected_team = "Team 2" if self.selected_team == "Team 1" else "Team 1"
                        self.selected_slot = -1
                else:
                    if event.key == pygame.K_LEFT:
                        self.selected_right = -1
                    elif event.key == pygame.K_UP:
                        self.selected_right = max(self.selected_right - 1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.selected_right = min(self.selected_right + 1, len(self.right_options) - 1)
                    elif event.key == pygame.K_RETURN:
                        self.activate_right_option()
                    elif event.key == pygame.K_TAB:
                        self.selected_team = "Team 2" if self.selected_team == "Team 1" else "Team 1"
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

    def activate_right_option(self):
        option = self.right_options[self.selected_right]
        team_option, action = option
        if team_option == "Battle":
            self.state = "battle_select"
        elif action == "quit":
            self.save_last_config()
            pygame.quit()
            sys.exit()
        else:
            if action == "control":
                current = self.settings[team_option]["control"]
                if current not in CONTROL_OPTIONS:
                    if current.lower() == "cyborg":
                        current = "Good Cyborg"
                    else:
                        current = CONTROL_OPTIONS[0]
                idx = CONTROL_OPTIONS.index(current)
                new_idx = (idx + 1) % len(CONTROL_OPTIONS)
                self.settings[team_option]["control"] = CONTROL_OPTIONS[new_idx]
            elif action == "save":
                self.universal_save(team_option)
            elif action == "load":
                self.universal_load(team_option)

    def save_last_config(self):
        config = {
            "mode": f"{self.settings['Team 1']['control']} vs {self.settings['Team 2']['control']}",
            "teams": self.teams,
            "team_names": self.team_names,
            "settings": self.settings
        }
        global _CACHED_CONFIG  # CACHING ADDED: обновляем кэш
        try:
            with open(SAVES_FILE, "r") as f:
                saves = json.load(f)
        except Exception as e:
            saves = {}
        saves["last_config"] = config
        _CACHED_CONFIG = config  # Обновляем кэш
        try:
            with open(SAVES_FILE, "w") as f:
                json.dump(saves, f)
            print("Last configuration saved.")
        except Exception as e:
            print("Error saving last configuration:", e)

    def handle_ship_select_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_ship_index = max(self.selected_ship_index - 1, 0)
                elif event.key == pygame.K_DOWN:
                    self.selected_ship_index = min(self.selected_ship_index + 1, len(self.ship_list) - 1)
                elif event.key == pygame.K_RETURN:
                    chosen_ship = self.ship_list[self.selected_ship_index]
                    if chosen_ship == "?":
                        chosen_ship = random.choice(list(SHIP_CLASSES.keys()))
                    self.teams[self.selected_team][self.selected_slot] = chosen_ship
                    self.state = "main_menu"
                elif event.key == pygame.K_ESCAPE:
                    self.state = "main_menu"

    def handle_team_name_edit_events(self):
        pass

    def universal_save(self, team):
        option = self.choose_save_option()
        if option is None:
            return
        if option == "New Save":
            name = self.prompt_for_save_name("Enter new profile name: ")
            if not name:
                return
        else:
            name = option
            if not self.prompt_confirm_overwrite(name):
                return
        config = {
            "fleet": self.teams[team],
            "team_name": self.team_names[team]
        }
        try:
            with open(SAVES_FILE, "r") as f:
                saves = json.load(f)
        except Exception as e:
            print("Read error:", e)
            saves = {}
        profiles = saves.get("profiles", {})
        profiles[name] = config
        saves["profiles"] = profiles
        try:
            with open(SAVES_FILE, "w") as f:
                json.dump(saves, f)
            print(f"Profile '{name}' saved.")
        except Exception as e:
            print("Write error:", e)

    def universal_load(self, team):
        profile_name = self.choose_profile()
        if not profile_name:
            return
        try:
            with open(SAVES_FILE, "r") as f:
                saves = json.load(f)
            profiles = saves.get("profiles", {})
            if profile_name in profiles:
                config = profiles[profile_name]
                self.teams[team] = config.get("fleet", self.teams[team])
                self.team_names[team] = config.get("team_name", self.team_names[team])
                self.normalize_teams()
                print(f"Profile '{profile_name}' loaded into {team}.")
        except Exception as e:
            print(e)

    def prompt_for_save_name(self, prompt_msg):
        save_name = ""
        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            text = self.font_menu.render(prompt_msg + save_name, True, WHITE)
            self.screen.blit(text, (50, SCREEN_H // 2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        waiting = False
                    elif event.key == pygame.K_BACKSPACE:
                        save_name = save_name[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        waiting = False
                        save_name = ""
                    else:
                        save_name += event.unicode
            self.clock.tick(30)
        return save_name

    def prompt_confirm_overwrite(self, profile_name):
        waiting = True
        confirm = False
        while waiting:
            self.screen.fill(BLACK)
            prompt = self.font_menu.render(f"Profile '{profile_name}' exists. Overwrite? (Y/N)", True, WHITE)
            self.screen.blit(prompt, (50, SCREEN_H // 2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        confirm = True
                        waiting = False
                    elif event.key == pygame.K_n:
                        confirm = False
                        waiting = False
            self.clock.tick(30)
        return confirm

    def prompt_confirm_delete(self, profile_name):
        waiting = True
        confirm = False
        while waiting:
            self.screen.fill(BLACK)
            prompt = self.font_menu.render(f"Delete profile '{profile_name}'? (Y/N)", True, WHITE)
            self.screen.blit(prompt, (50, SCREEN_H // 2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        confirm = True
                        waiting = False
                    elif event.key == pygame.K_n:
                        confirm = False
                        waiting = False
            self.clock.tick(30)
        return confirm

    def delete_profile(self, profile_name):
        try:
            with open(SAVES_FILE, "r") as f:
                saves = json.load(f)
            profiles = saves.get("profiles", {})
            if profile_name in profiles:
                del profiles[profile_name]
                saves["profiles"] = profiles
                with open(SAVES_FILE, "w") as f:
                    json.dump(saves, f)
                print(f"Profile '{profile_name}' deleted.")
        except Exception as e:
            print("Error deleting profile:", e)

    def choose_save_option(self):
        try:
            with open(SAVES_FILE, "r") as f:
                saves = json.load(f)
            profiles = saves.get("profiles", {})
            keys = list(profiles.keys())
            keys.sort()
            keys.append("New Save")
        except Exception as e:
            keys = ["New Save"]
        selected_index = 0
        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            title = self.font_title.render("Select Save Profile", True, YELLOW)
            self.screen.blit(title, (50, 50))
            for i, key in enumerate(keys):
                color = YELLOW if i == selected_index else WHITE
                text = self.font_small.render(key, True, color)
                self.screen.blit(text, (50, 150 + i * 40))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_index = max(selected_index - 1, 0)
                    elif event.key == pygame.K_DOWN:
                        selected_index = min(selected_index + 1, len(keys) - 1)
                    elif event.key == pygame.K_RETURN:
                        waiting = False
                        return keys[selected_index]
                    elif event.key == pygame.K_ESCAPE:
                        waiting = False
                        return None
            self.clock.tick(30)

    def choose_profile(self):
        try:
            with open(SAVES_FILE, "r") as f:
                saves = json.load(f)
            profiles = saves.get("profiles", {})
            keys = list(profiles.keys())
            if not keys:
                return None
            keys.sort()
        except Exception as e:
            print(e)
            return None
        selected_index = 0
        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            title = self.font_title.render("Select Profile", True, YELLOW)
            self.screen.blit(title, (50, 50))
            for i, key in enumerate(keys):
                color = YELLOW if i == selected_index else WHITE
                text = self.font_small.render(key, True, color)
                self.screen.blit(text, (50, 150 + i * 40))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_index = max(selected_index - 1, 0)
                    elif event.key == pygame.K_DOWN:
                        selected_index = min(selected_index + 1, len(keys) - 1)
                    elif event.key == pygame.K_DELETE:
                        profile_to_delete = keys[selected_index]
                        if self.prompt_confirm_delete(profile_to_delete):
                            self.delete_profile(profile_to_delete)
                            try:
                                with open(SAVES_FILE, "r") as f:
                                    saves = json.load(f)
                                profiles = saves.get("profiles", {})
                                keys = list(profiles.keys())
                                keys.sort()
                                if not keys:
                                    waiting = False
                                    return None
                                selected_index = 0
                            except Exception as e:
                                print(e)
                                waiting = False
                                return None
                    elif event.key == pygame.K_RETURN:
                        waiting = False
                        return keys[selected_index]
                    elif event.key == pygame.K_ESCAPE:
                        waiting = False
                        return None
            self.clock.tick(30)

    def display_loop(self):
        while True:
            if self.state == "main_menu":
                self.handle_main_events()
                self.draw_main_menu()
            elif self.state == "ship_select":
                self.handle_ship_select_events()
                self.draw_ship_select()
            elif self.state == "team_name_edit":
                pass
            elif self.state == "battle_select":
                config = self.battle_select_mode()
                return config
            elif self.state == "exit":
                config = {
                    "mode": f"{self.settings['Team 1']['control']} vs {self.settings['Team 2']['control']}",
                    "teams": self.teams,
                    "team_names": self.team_names,
                    "settings": self.settings
                }
                self.save_last_config()
                return config
            pygame.display.flip()
            self.clock.tick(30)

    def display(self):
        return self.display_loop()


class PauseMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font_title = pygame.font.SysFont("Arial",48)
        self.font_menu = pygame.font.SysFont("Arial",36)
        self.font_small = pygame.font.SysFont("Arial",24)
        self.options = ["Resume", "Main Menu", "Quit"]
        self.selected = 0

    def display(self):
        while True:
            self.screen.fill((20,20,20))
            left_rect = pygame.Rect(0, 0, GAME_SCREEN_W, SCREEN_H)
            pygame.draw.rect(self.screen, (30,30,30), left_rect)
            title_surface = self.font_title.render("Pause", True, YELLOW)
            self.screen.blit(title_surface, (20,20))
            right_rect = pygame.Rect(GAME_SCREEN_W, 0, PANEL_WIDTH, SCREEN_H)
            pygame.draw.rect(self.screen, (40,40,40), right_rect)
            option_height = 50
            spacing = 10
            start_y = 100
            for idx, option in enumerate(self.options):
                rect = pygame.Rect(right_rect.x+10, start_y+idx*(option_height+spacing), right_rect.width-20, option_height)
                if idx == self.selected:
                    pygame.draw.rect(self.screen, YELLOW, rect, 2)
                else:
                    pygame.draw.rect(self.screen, GRAY, rect, 1)
                text_surface = self.font_menu.render(option, True, WHITE)
                self.screen.blit(text_surface, (rect.x+5, rect.y+10))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = max(self.selected-1,0)
                    elif event.key == pygame.K_DOWN:
                        self.selected = min(self.selected+1, len(self.options)-1)
                    elif event.key == pygame.K_RETURN:
                        return self.options[self.selected]
                    elif event.key == pygame.K_ESCAPE:
                        return "Resume"
            self.clock.tick(30)


def fast_load_menu(screen, clock):
    """
    Быстрый переход в главное меню после завершения битвы:
    создаёт новый экземпляр SuperMeleeMenu, сбрасывает его состояние и немедленно генерирует конфигурацию главного меню.
    При этом кэширование конфигурации применяется для минимизации операций с файлами.
    """
    menu = SuperMeleeMenu(screen, clock)
    menu.reset()  # Сброс состояния меню в "main_menu"
    config = menu.generate_config()  # Немедленная генерация конфигурации главного меню
    menu.save_last_config()
    return config


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    # Для обычного тестирования:
    menu = SuperMeleeMenu(screen, clock)
    config = menu.display()  # Стандартное интерактивное меню
    # Или можно использовать fast_load_menu(screen, clock) для быстрого перехода в главное меню
    print("Config loaded:", config)
