import os
import time

import curses

from level import LevelGenerator, Level, Tile
from color import Color
from player import Player
from game_object import LightSource, Enemy, Chest, Heal
from vec2 import Vec2
from ui_utils import Message, LOGO_1, LOGO_2


class Game:
    FPS_60 = 1/60
    SCR_W = 100
    SCR_H = 30
    SYMBOL_ASPECT = 9 / 19
    LIGHT = '░▒▓█'

    STATE_WALK = 1
    STATE_BATTLE = 2
    STATE_LOSE = 3
    STATE_MENU = 4

    def __init__(self, debug=False):
        os.system(f'mode {self.SCR_W},{self.SCR_H+1}')

        self.debug = debug
        self.debug_ui = False
        self.debug_no_fog = False

        self.scr: curses.window = None
        self.delta_time = 0.
        self.is_running = False

        self.game_record = 0
        self.is_first_game = False

        self.current_level: Level = None
        self.current_level_number = 0
        self.player: Player = Player()
        self.current_state = self.STATE_MENU
        self.current_enemy: Enemy = None
        self.battle: Battle = None

        self.messages_queue = []
        self.current_message = None
        self.msg_time_left = 0

        self.losescr: Lose = None
        self.menuscr: Menu = None

    def _init_color_palette(self):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_WHITE)
        curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(12, curses.COLOR_WHITE, curses.COLOR_WHITE)
        curses.init_pair(13, curses.COLOR_RED, curses.COLOR_WHITE)
        self._colors = {
            Color.White: curses.color_pair(1),
            Color.Red: curses.color_pair(2),
            Color.Green: curses.color_pair(3),
            Color.Blue: curses.color_pair(4),
            Color.Yellow: curses.color_pair(5),
            Color.Cyan: curses.color_pair(6),
            Color.Magenta: curses.color_pair(7),
            Color.Black: curses.color_pair(8),
            Color.BlackOnWhite: curses.color_pair(9),
            Color.GreenOnWhite: curses.color_pair(10),
            Color.BlackOnGreen: curses.color_pair(11),
            Color.WhiteOnWhite: curses.color_pair(12),
            Color.RedOnWhite: curses.color_pair(13),
        }

    def clr(self, color_id):
        return self._colors[color_id]

    def _load(self):
        create_new = False
        try:
            with open('save.txt', 'r') as f:
                ints = list(map(lambda x: int(x.strip()), f.readlines()))
            if len(ints) != 2:
                create_new = True
            else:
                self.game_record = ints[0]
                self.is_first_game = bool(ints[1])
        except:
            create_new = True

        if create_new:
            self.game_record = 0
            self.is_first_game = True
            self._save()

    def _save(self):
        with open('save.txt', 'w') as f:
            f.write(f'{self.game_record}\n')
            f.write(f'{int(self.is_first_game)}\n')

    def _update_record(self):
        score = self.player.get_score()
        if score > self.game_record:
            self.game_record = score
            self._save()

    def run(self, stdscr: curses.window):
        self._init_color_palette()
        self.scr = stdscr
        self.menuscr = Menu(self, self.scr)
        self.is_running = True
        self.scr.nodelay(True)

        self._load()

        self.delta_time = 0.001
        while self.is_running:
            dt = time.time()
            key = self.scr.getch()
            if key != -1:
                self._handle_key(key)
            self._update()
            if self.current_state == self.STATE_WALK:
                self._draw()
            elif self.current_state == self.STATE_BATTLE:
                self._draw_battle_screen()
            elif self.current_state == self.STATE_LOSE:
                self._draw_lose_screen()

            if self.current_state == self.STATE_MENU:
                self._draw_menu_screen()
            else:
                if self.is_first_game:
                    if self.current_state == self.STATE_WALK:
                        self._draw_tutorial_ui()
                    elif self.current_state == self.STATE_BATTLE:
                        self._draw_tutorial_battle_ui()
                self._draw_ui()
            self.delta_time = time.time() - dt
            t = time.time()
            if self.delta_time < self.FPS_60:
                time.sleep(self.FPS_60 - self.delta_time)
            self.delta_time += time.time() - t

    def restart_game(self):
        self.player: Player = Player()

        self.current_level: Level = None
        self.current_level_number = 0
        self.next_level()

        self.current_state = self.STATE_WALK
        self.current_enemy: Enemy = None
        self.battle: Battle = None
        self.messages_queue = []
        self.current_message = None
        self.msg_time_left = 0

    def _handle_key(self, key_code: int):
        if key_code == 27:  # ESCAPE
            self.current_state = self.STATE_MENU
            return
        if self.debug and self.current_state == self.STATE_BATTLE:
            if key_code == curses.KEY_F3:
                self.finish_battle()
        if self.debug:
            if key_code == curses.KEY_F1:
                self.debug_ui = not self.debug_ui
                return
            if key_code == curses.KEY_F2:
                self.debug_no_fog = not self.debug_no_fog
                return
            if key_code == curses.KEY_F4:
                self.player.take_dmg(10**4)
                return
        if self.current_state == self.STATE_WALK:
            if key_code == curses.KEY_UP:
                move_vec = Vec2(0, -1)
                self.move_player(self.player.get_coords() + move_vec)
            elif key_code == curses.KEY_DOWN:
                move_vec = Vec2(0, 1)
                self.move_player(self.player.get_coords() + move_vec)
            elif key_code == curses.KEY_RIGHT:
                move_vec = Vec2(1, 0)
                self.move_player(self.player.get_coords() + move_vec)
            elif key_code == curses.KEY_LEFT:
                move_vec = Vec2(-1, 0)
                self.move_player(self.player.get_coords() + move_vec)
            elif key_code in (81, 113):
                coords = self.player.get_coords()
                if self.player.remove_light():
                    self.current_level.place_object(coords, LightSource(3))
        if self.current_state == self.STATE_BATTLE:
            self.battle.input_key(key_code)
        elif self.current_state == self.STATE_LOSE:
            self.losescr.input_key(key_code)
        elif self.current_state == self.STATE_MENU:
            self.menuscr.input_key(key_code)

    def move_player(self, new_coords: Vec2):
        t = time.time()
        if t > self.player.next_move:
            self.player.next_move = t + self.player.move_delay
            (tile_id, _, _), obj, enemy = self.current_level.get_all(new_coords)
            if obj is None and enemy is None:
                if tile_id == Tile.id_Floor:
                    self.player.move_to(new_coords)
                elif tile_id == Tile.id_Exit:
                    if self.is_first_game:
                        self.is_first_game = False
                        self._save()
                        self.restart_game()
                    else:
                        self.next_level()
            else:
                self.player.move_to(new_coords)
                if obj is not None:
                    if isinstance(obj, LightSource) and self.player.get_max_lights_count() > self.player.get_lights_count():
                        self.player.add_light()
                        self.current_level.remove_object(obj)
                        self._show_msg(Message.text(Message.PickLight))
                    elif isinstance(obj, Chest):
                        upgrade = Chest.get_upgrade()
                        self.current_level.remove_object(obj)
                        self.apply_player_upgrade(upgrade)
                    elif isinstance(obj, Heal):
                        self.current_level.remove_object(obj)
                        self.player.heal()
                        self._show_msg(Message.text(Message.PickHeal))
                if enemy is not None:
                    self.start_battle(enemy)

    def apply_player_upgrade(self, upgrade):
        res = self.player.apply_upgrade(upgrade)
        if upgrade == Chest.LightsAmountUpgrade:
            msg = Message.text(Message.PickUpgradeLightAmount)
        elif upgrade == Chest.LightLevelUpgrade:
            msg = Message.text(Message.PickUpgradeLightLevel)
        elif upgrade == Chest.BattleTimeUpgrade:
            msg = Message.text(Message.PickUpgradeTimeLimit)
        elif upgrade == Chest.MaxHPUpgrage:
            msg = Message.text(Message.PickUpgradeHP)
        else:
            return
        self._show_msg(msg[res])

    def start_battle(self, enemy):
        self.player.reset_time_left()
        self.current_enemy = enemy
        self.current_state = self.STATE_BATTLE
        self.battle = Battle(self, self.scr, Vec2(2, 2), Vec2(self.SCR_W - 3, self.SCR_H - 3))

    def finish_battle(self):
        if self.current_state != self.STATE_BATTLE:
            return
        reward = (1 + self.current_enemy.get_difficulty()) * 100
        self._show_msg(f'Украдено: {reward}¥')
        self.player.add_score(reward)
        self.current_level.remove_enemy(self.current_enemy)
        self.current_enemy = None
        self.current_state = self.STATE_WALK
        self.battle = None

    def next_level(self):
        if self.current_level is not None:
            self.player.add_score(1000)
            self._show_msg('Следующий уровень. Украдено 1000¥')

        if self.is_first_game:
            for _ in range(6):
                self.player.upgrade_time_limit()
            self.current_level = LevelGenerator.generate_tutorial_room(self.SCR_W, self.SCR_H)
            # self.current_level = LevelGenerator.generate_test_room(self.SCR_W, self.SCR_H)
        else:
            self.current_level_number += 1
            if self.current_level_number >= 25:
                walls_destroy_chance = 0
            else:
                walls_destroy_chance = -self.current_level_number/25 + 1
            self.current_level = LevelGenerator.generate_labirinth(self.SCR_W, self.SCR_H, walls_destroy_chance)
            self.current_level.spawn_objects()
            self.current_level.spawn_enemy(1+self.current_level_number//4, self.current_level_number//2)
        self.player.move_to(self.current_level.get_spawn_point())
        self.player.restore_all_lights()

    def calc_light(self):
        light_map = []
        for y in range(self.SCR_H):
            light_map.append([])
            for x in range(self.SCR_W):
                if self.debug_no_fog:
                    light_map[y].append(4)
                else:
                    light_map[y].append(0)
        if not self.debug_no_fog:
            for light_source in self.current_level.get_light_sources() + [self.player.light_source]:
                source_coords = light_source.get_coords()
                light_source.set_radius(self.player.light_radius)
                lighting = light_source.get_lighting(self.SYMBOL_ASPECT)
                for offset, strength in lighting:
                    coords: Vec2 = offset + source_coords
                    if 0 <= coords.x < self.SCR_W and 0 <= coords.y < self.SCR_H:
                        light_at_point = light_map[coords.y][coords.x]
                        light_at_point += strength
                        if light_at_point > 4:
                            light_at_point = 4
                        light_map[coords.y][coords.x] = light_at_point
        return light_map

    def _update(self):
        if self.current_message is not None:
            self.msg_time_left -= self.delta_time
            if self.msg_time_left <= 0:
                self.current_message = None
                self.msg_time_left = 0
        if self.current_message is None and len(self.messages_queue) > 0:
            self.current_message, show_time = self.messages_queue.pop(0)
            self.msg_time_left = show_time

        if self.current_state == self.STATE_BATTLE:
            if self.battle.is_done():
                self.finish_battle()
            else:
                if self.player.get_time_left() <= 0:
                    self.player.take_dmg(1 * self.delta_time)
                else:
                    self.player.reduce_time_left(self.delta_time)

        if (self.current_state != self.STATE_MENU
                and self.player.get_hp() <= 0
                and self.current_state != self.STATE_LOSE):
            self.current_state = self.STATE_LOSE
            score = self.player.get_score()
            self._update_record()
            width = max(len(Message.text(Message.LoseTitle)), len(f'Заработано: {score}¥'))
            upleft = Vec2(self.SCR_W//2 - width//2 - 1, self.SCR_H//2 - 5)
            downright = Vec2(self.SCR_W//2 + width//2 + 2, self.SCR_H//2 + 5)
            self.losescr = Lose(self, self.scr, upleft, downright, score)

    def _show_msg(self, msg, show_time=1.5):
        self.messages_queue.append((msg, show_time))

    def _draw_at(self, coords: Vec2, string, clr=Color.White):
        if 0 <= coords.x < self.SCR_W and 0 <= coords.y < self.SCR_H:
            self.scr.addstr(coords.y, coords.x, string, self.clr(clr))

    def _draw(self):
        lighting = self.calc_light()
        self.scr.clear()
        for y in range(self.SCR_H):
            for x in range(self.SCR_W):
                l = lighting[y][x]
                if l > 0:
                    coords = Vec2(x, y)
                    (tile_id, tile_ch, tile_clr), obj, enemy = self.current_level.get_all(coords)
                    if obj is None and enemy is None:
                        # отрисовка карты
                        if tile_id == Tile.id_Wall:
                            tile_ch = self.LIGHT[l-1]
                        elif tile_id == Tile.id_Floor and self.debug_ui:
                            tile_ch = str(l)
                            tile_clr = Color.Green
                        self._draw_at(coords, tile_ch, tile_clr)
                    elif enemy is None:
                        # отрисовка объектов
                        obj_ch, obj_clr = obj.get_char()
                        self._draw_at(coords, obj_ch, obj_clr)
                    else:
                        # отрисовка врагов
                        enemy_ch, enemy_clr = enemy.get_char()
                        self._draw_at(coords, enemy_ch, enemy_clr)

        # отрисовка игрока
        ch, clr = self.player.get_char()
        self._draw_at(self.player.get_coords(), ch, clr)

    def _draw_ui(self):
        self._draw_at(Vec2(0, 0), ' '*self.SCR_W, Color.BlackOnWhite)

        l_count = self.player.get_lights_count()
        l_max_count = self.player.get_max_lights_count()
        l_level = self.player.get_light_level()
        ui_str = f'Фонари ({l_level} ур): {l_count}/{l_max_count}'
        self._draw_at(Vec2(0, 0), ui_str, Color.BlackOnWhite)
        ui_str_len = len(ui_str)

        hp = self.player.get_hp()
        max_hp = self.player.get_max_hp()
        ui_str = f'HP: {hp:.0f}/{max_hp}'
        if hp/max_hp <= 0.1:
            clr = Color.RedOnWhite
        else:
            clr = Color.BlackOnWhite
        self._draw_at(Vec2(ui_str_len+2, 0), ui_str, clr)
        ui_str_len += len(ui_str) + 2

        time_lim = self.player.get_time_limit()
        ui_str = f'DT: {time_lim}с'
        self._draw_at(Vec2(ui_str_len+2, 0), ui_str, Color.BlackOnWhite)

        score = self.player.get_score()
        ui_str = f'{score}¥'
        score_len = len(ui_str)
        self._draw_at(Vec2(self.SCR_W-score_len-1, 0), ui_str, Color.BlackOnWhite)

        if self.current_message is not None:
            self._draw_at(Vec2(0, 1), self.current_message, Color.BlackOnGreen)

        if self.debug_ui:
            _str = f'Frame: {self.delta_time:.4f}s'
            if self.delta_time > 0.00001:
                _str += f' FPS: {1 / self.delta_time:.0f}'
            else:
                _str += 'FPS: inf'
            self._draw_at(Vec2(0, self.SCR_H-1), _str, Color.GreenOnWhite)

    def _draw_battle_screen(self):
        self.battle.draw()

    def _draw_lose_screen(self):
        self.losescr.draw()

    def _draw_menu_screen(self):
        self.scr.clear()
        self.menuscr.draw()

    def _draw_tutorial_ui(self):
        self._draw_at(Vec2(16, 1), '↑', Color.Cyan)
        self._draw_at(Vec2(1, 2), 'Количество фонарей', Color.Cyan)
        self._draw_at(Vec2(1, 3), 'и их уровень', Color.Cyan)
        self._draw_at(Vec2(1, 4), 'Чем больше уровень', Color.Cyan)
        self._draw_at(Vec2(1, 5), 'тем дальше видно', Color.Cyan)

        self._draw_at(Vec2(26, 1), '↑', Color.Cyan)
        self._draw_at(Vec2(20, 2), 'Ваше здоровье', Color.Cyan)
        self._draw_at(Vec2(20, 3), 'Если оно', Color.Cyan)
        self._draw_at(Vec2(20, 4), 'опустится до 0', Color.Cyan)
        self._draw_at(Vec2(20, 5), 'вы проиграете', Color.Cyan)

        self._draw_at(Vec2(36, 1), '↑', Color.Cyan)
        self._draw_at(Vec2(36, 2), 'Время обнаружения', Color.Cyan)
        self._draw_at(Vec2(36, 3), 'Это время, за которое', Color.Cyan)
        self._draw_at(Vec2(36, 4), 'можно безопасно взломать', Color.Cyan)
        self._draw_at(Vec2(36, 5), 'систему защиты', Color.Cyan)

        self._draw_at(Vec2(self.SCR_W - 3, 1), '↑', Color.Cyan)
        self._draw_at(Vec2(self.SCR_W - 23, 2), 'Количество украденных', Color.Cyan)
        self._draw_at(Vec2(self.SCR_W - 23, 3), 'средств', Color.Cyan)

        self._draw_at(Vec2(2, 12), '↑', Color.Cyan)
        self._draw_at(Vec2(1, 13), '@ - это вы.', Color.Cyan)
        self._draw_at(Vec2(1, 14), 'Вы - компьютерный вирус', Color.Cyan)
        self._draw_at(Vec2(1, 15), 'в банковской системе.', Color.Cyan)
        self._draw_at(Vec2(1, 16), 'Ваша цель - украсть', Color.Cyan)
        self._draw_at(Vec2(1, 17), 'как можно больше средств.', Color.Cyan)

        self._draw_at(Vec2(1, 19), 'Используйте стрелки,', Color.Cyan)
        self._draw_at(Vec2(1, 20), 'чтобы передвигаться.', Color.Cyan)
        self._draw_at(Vec2(1, 22), 'Используйте Q,', Color.Cyan)
        self._draw_at(Vec2(1, 23), 'чтобы оставить фонарь.', Color.Cyan)
        self._draw_at(Vec2(1, 24), 'Тут темновато, это', Color.Cyan)
        self._draw_at(Vec2(1, 25), 'поможет ориентироваться.', Color.Cyan)
        self._draw_at(Vec2(1, 26), 'Они восстанавливаются при', Color.Cyan)
        self._draw_at(Vec2(1, 27), 'переходе на новый уровень.', Color.Cyan)

        self._draw_at(Vec2(29, 12), '↑', Color.Cyan)
        self._draw_at(Vec2(28, 13), '§ - это процессы', Color.Cyan)
        self._draw_at(Vec2(28, 14), 'защитной системы.', Color.Cyan)
        self._draw_at(Vec2(28, 15), 'Взламывайте их,', Color.Cyan)
        self._draw_at(Vec2(28, 16), 'чтобы украсть', Color.Cyan)
        self._draw_at(Vec2(28, 17), 'средства.', Color.Cyan)
        self._draw_at(Vec2(28, 19), 'Если получили урон,', Color.Cyan)
        self._draw_at(Vec2(28, 20), 'подбирайте +, чтобы', Color.Cyan)
        self._draw_at(Vec2(28, 21), 'восстановить HP.', Color.Cyan)

        self._draw_at(Vec2(49, 12), '↑', Color.Cyan)
        self._draw_at(Vec2(49, 13), '■ - это контейнеры', Color.Cyan)
        self._draw_at(Vec2(49, 14), 'с улучшениями.', Color.Cyan)
        self._draw_at(Vec2(49, 15), 'Могут содержать:', Color.Cyan)
        self._draw_at(Vec2(49, 16), '-улучшение фонарей', Color.Cyan)
        self._draw_at(Vec2(49, 17), '-увеличение кол-ва', Color.Cyan)
        self._draw_at(Vec2(49, 18), 'фонарей', Color.Cyan)
        self._draw_at(Vec2(49, 19), '-увеличение HP', Color.Cyan)
        self._draw_at(Vec2(49, 20), '-увеличение DT', Color.Cyan)

        self._draw_at(Vec2(69, 13), 'Пройдите до конца коридора.', Color.Cyan)
        self._draw_at(Vec2(69, 14), 'Здесь вы увидите дверь,', Color.Cyan)
        self._draw_at(Vec2(69, 15), 'ведущую на следующий уровень.', Color.Cyan)
        self._draw_at(Vec2(69, 16), 'Проходите через них, чтобы', Color.Cyan)
        self._draw_at(Vec2(69, 17), 'продвигаться дальше.', Color.Cyan)
        self._draw_at(Vec2(69, 18), 'С каждым уровнем', Color.Cyan)
        self._draw_at(Vec2(69, 19), 'через систему будет сложнее', Color.Cyan)
        self._draw_at(Vec2(69, 20), 'пробираться и защитные', Color.Cyan)
        self._draw_at(Vec2(69, 21), 'системы будут становиться', Color.Cyan)
        self._draw_at(Vec2(69, 22), 'устойчивее ко взлому.', Color.Cyan)

    def _draw_tutorial_battle_ui(self):
        self._draw_at(Vec2(36, 5), 'Уровень защитной системы определяет сложность взлома,', Color.Cyan)
        self._draw_at(Vec2(36, 6), 'цену ошибки при взломе (вы получаете урон при ошибках)', Color.Cyan)
        self._draw_at(Vec2(36, 7), 'и размер награды.', Color.Cyan)
        self._draw_at(Vec2(36, 9), 'Время до обнаружения: по истечение этого времени вы начнете', Color.Cyan)
        self._draw_at(Vec2(36, 10), 'получать постоянный урон.', Color.Cyan)
        self._draw_at(Vec2(36, 12), 'Чтобы взломать систему, вводите код слева.', Color.Cyan)
        self._draw_at(Vec2(36, 13), 'Каждую строчку нужно отправлять на исполнение,', Color.Cyan)
        self._draw_at(Vec2(36, 14), 'нажимая Enter.', Color.Cyan)
        self._draw_at(Vec2(36, 16), 'Попробуйте!', Color.Cyan)


class Menu:
    def __init__(self, game: Game, stdscr: curses.window):
        self.game = game
        self.scr = stdscr
        self.width = self.game.SCR_W
        self.height = self.game.SCR_H

        self.logo_t = 0
        self.logo_underline = False

        self.start_or_exit = True

    def draw(self):
        self._draw_logo()

        str_start = 'Начать'
        str_exit = 'Выход'

        if self.start_or_exit:
            clr1, clr2 = Color.BlackOnWhite, Color.White
        else:
            clr1, clr2 = Color.White, Color.BlackOnWhite
        offset = max(len(str_start), len(str_exit))
        x = self.width//2 - offset
        y = self.height//2
        self.draw_at(Vec2(x, y), str_start, clr1)
        x = self.width//2 - offset
        y = self.height//2 + 2
        self.draw_at(Vec2(x, y), str_exit, clr2)

        if self.game.game_record > 0:
            x = self.width//2 - offset
            y = self.height//2 - 2
            str_record = f'Рекорд: {self.game.game_record}¥'
            self.draw_at(Vec2(x, y), str_record, Color.White)

    def _draw_logo(self):
        t = time.time()
        if t - self.logo_t > 1:
            self.logo_underline = not self.logo_underline
            self.logo_t = t

        logo = LOGO_1 if self.logo_underline else LOGO_2
        logo_len = len(logo[0])
        padding = (self.width - logo_len)//2
        for i, logo_str in enumerate(logo):
            self.draw_at(Vec2(padding, 1+i), logo_str, Color.Green)

    def draw_at(self, coords: Vec2, string, color):
        self.scr.addstr(coords.y, coords.x, string, self.game.clr(color))

    def input_key(self, key_code):
        if key_code in (curses.KEY_UP, curses.KEY_DOWN):
            self.start_or_exit = not self.start_or_exit
        elif key_code == 10:
            if self.start_or_exit:
                self.game.restart_game()
            else:
                self.game.is_running = False


class Lose:
    def __init__(self, game: Game, stdscr: curses.window, upleft: Vec2, botright: Vec2, score):
        self.game = game
        self.scr = stdscr
        self.score = score
        self.offset = upleft
        size = botright - upleft + 1
        self.width = size.x
        self.height = size.y

        self.restart_or_menu = True

    def draw(self):
        self.draw_window()
        self.draw_ui()

    def draw_at(self, coords: Vec2, string, color):
        coords += self.offset
        self.scr.addstr(coords.y, coords.x, string, self.game.clr(color))

    def draw_window(self, color=Color.White):
        for y in range(self.height):
            for x in range(self.width):
                if y == 0 and x == 0:
                    self.draw_at(Vec2(x, y), '╔', color)
                elif y == 0 and x == self.width-1:
                    self.draw_at(Vec2(x, y), '╗', color)
                elif y == self.height-1 and x == 0:
                    self.draw_at(Vec2(x, y), '╚', color)
                elif y == self.height-1 and x == self.width-1:
                    self.draw_at(Vec2(x, y), '╝', color)
                elif y == 0 or y == self.height-1:
                    self.draw_at(Vec2(x, y), '═', color)
                elif x == 0 or x == self.width-1:
                    self.draw_at(Vec2(x, y), '║', color)
                else:
                    self.draw_at(Vec2(x, y), ' ', color)

    def draw_ui(self):
        self.draw_at(Vec2(2, 2), Message.text(Message.LoseTitle), Color.White)
        self.draw_at(Vec2(2, 4), f'Заработано: {self.score}¥', Color.White)
        if self.restart_or_menu:
            self.draw_at(Vec2(2, 6), f'Начать заново', Color.BlackOnWhite)
            self.draw_at(Vec2(2, 8), f'Меню', Color.White)
        else:
            self.draw_at(Vec2(2, 6), f'Начать заново', Color.White)
            self.draw_at(Vec2(2, 8), f'Меню', Color.BlackOnWhite)

    def input_key(self, key_code):
        if key_code in (curses.KEY_UP, curses.KEY_DOWN):
            self.restart_or_menu = not self.restart_or_menu
        elif key_code == 10:
            if self.restart_or_menu:
                self.game.restart_game()
            else:
                self.game.current_state = self.game.STATE_MENU


class Battle:
    def __init__(self, game: Game, stdscr: curses.window, upleft: Vec2, botright: Vec2):
        self.game = game
        self.enemy = self.game.current_enemy
        self.player = self.game.player
        self.scr = stdscr
        self.offset = upleft
        size = botright - upleft + 1
        self.width = size.x
        self.height = size.y
        self.input_coords = Vec2(1, self.height-2)

        self._done = False

        self.code_list = self.enemy.get_code_list()
        self.cur_line = 0
        self.cur_symbol = 0
        self.end_line = False
        self.next_err = False
        self.input = ''

    def is_done(self):
        return self._done

    def draw(self):
        self.draw_window()
        self.draw_input()
        self.draw_ui()

    def draw_at(self, coords: Vec2, string, color):
        coords += self.offset
        self.scr.addstr(coords.y, coords.x, string, self.game.clr(color))

    def draw_window(self, color=Color.White):
        for y in range(self.height):
            for x in range(self.width):
                if y == 0 and x == 0:
                    self.draw_at(Vec2(x, y), '╔', color)
                elif y == 0 and x == self.width-1:
                    self.draw_at(Vec2(x, y), '╗', color)
                elif y == self.height-1 and x == 0:
                    self.draw_at(Vec2(x, y), '╚', color)
                elif y == self.height-1 and x == self.width-1:
                    self.draw_at(Vec2(x, y), '╝', color)
                elif y == self.height-3 and x == 0:
                    self.draw_at(Vec2(x, y), '╠', color)
                elif y == self.height-3 and x == self.width-1:
                    self.draw_at(Vec2(x, y), '╣', color)
                elif y == 0 or y == self.height-3 or y == self.height-1:
                    self.draw_at(Vec2(x, y), '═', color)
                elif x == 0 or x == self.width-1:
                    self.draw_at(Vec2(x, y), '║', color)
                else:
                    self.draw_at(Vec2(x, y), ' ', color)

    def draw_ui(self):
        self.draw_at(Vec2(1, 1), f'Взлом процесса защитной системы (ур. {self.enemy.get_difficulty()})', Color.White)
        self.draw_at(Vec2(1, 2), f'Времени до обнаружения: {self.player.get_time_left():.0f} сек'.ljust(self.width-2),
                     Color.White)
        for i, line in enumerate(self.code_list):
            coords = Vec2(3, 4 + i)
            if i < self.cur_line:
                self.draw_at(coords, line[:-1], Color.Green)
            elif i == self.cur_line:
                line_part = line[:self.cur_symbol]
                self.draw_at(coords, line_part, Color.Green)
                coords.x += len(line_part)
                self.draw_at(coords, line[self.cur_symbol:-1], Color.White)
                if self.next_err:
                    if self.cur_symbol < len(line)-1:
                        self.draw_at(coords, line[self.cur_symbol], Color.Red)
                    else:
                        coords = Vec2(self.input_coords.x, self.input_coords.y)
                        msg = 'PRESS ENTER TO SEND'
                        coords.x = self.width - 2 - len(msg)
                        self.draw_at(coords, msg, Color.Red)
            else:
                if self.game.debug_ui:
                    self.draw_at(coords, line[:-1], Color.White)
                else:
                    self.draw_at(coords, '?'*len(line), Color.White)

    def draw_input(self):
        self.draw_at(self.input_coords, self.input.ljust(self.width-2), Color.White)

    def input_key(self, key_code):
        if key_code == 10:
            key = '\n'
        else:
            key = curses.keyname(key_code).decode('UTF-8')
        if key in ('KEY_DOWN', 'KEY_UP', 'KEY_RIGHT', 'KEY_LEFT'):
            return

        if self.code_list[self.cur_line][self.cur_symbol] == key:
            self.next_err = False
            self.input += key
            self.cur_symbol += 1
            if self.cur_symbol >= len(self.code_list[self.cur_line]):
                self.input = ''
                self.cur_symbol = 0
                self.cur_line += 1
                if self.cur_line >= len(self.code_list):
                    self._done = True
        else:
            self.player.take_dmg(self.enemy.dmg)
            self.next_err = True
