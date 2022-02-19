import random

from game_object import GameObject, LightSource, Enemy, Chest, Heal
from color import Color
from vec2 import Vec2


class Tile:
    id_Floor = 0
    id_Wall = 1
    id_PlayerSpawn = 2
    id_Exit = 3

    _tile_chars = {
        id_Floor: ' ',
        id_Wall: '█',
        id_PlayerSpawn: 'S',
        id_Exit: '█',
    }

    _tile_colors = {
        id_Floor: Color.Black,
        id_Wall: Color.White,
        id_PlayerSpawn: Color.Green,
        id_Exit: Color.Yellow,
    }

    @classmethod
    def get_tile(cls, tile):
        return cls._tile_chars.get(tile, '╳'), cls._tile_colors.get(tile, Color.White)


class Level:
    def __init__(self, lvl_map):
        self._map = lvl_map
        self._objects = {}
        self._enemies = {}
        self._light_sources = []
        self._height = len(self._map)
        self._width = len(self._map[0])
        self._spawn_point: Vec2 = None
        for y in range(self._height):
            for x in range(self._width):
                if self._map[y][x] == Tile.id_PlayerSpawn:
                    self._spawn_point = Vec2(x, y)
                    self._map[y][x] = Tile.id_Floor
        if self._spawn_point is None:
            raise Exception("No spawn point on level")

    def get_spawn_point(self):
        return self._spawn_point

    def _get_tile_id(self, coords: Vec2):
        if 0 <= coords.x <= self._width and 0 <= coords.y <= self._height:
            return self._map[coords.y][coords.x]
        else:
            raise Exception("Attempt of getting tile id outside the map")

    def get_all(self, coords: Vec2):
        return self.get_tile(coords), self.get_object(coords), self.get_enemy(coords)

    def get_tile(self, coords: Vec2):
        tile_id = self._get_tile_id(coords)
        tile_ch, tile_clr = Tile.get_tile(tile_id)
        return tile_id, tile_ch, tile_clr

    def place_object(self, coords: Vec2, obj: GameObject):
        obj.move_to(coords)
        if isinstance(obj, LightSource):
            self._light_sources.append(obj)
        if coords in self._objects:
            cur_obj = self._objects[coords]
            if isinstance(cur_obj, LightSource):
                self._light_sources.remove(cur_obj)
        self._objects[coords] = obj

    def remove_object(self, obj: GameObject):
        coords = obj.get_coords()
        if coords in self._objects and self._objects[coords] == obj:
            del self._objects[coords]
            if isinstance(obj, LightSource):
                self._light_sources.remove(obj)

    def get_object(self, coords: Vec2):
        return self._objects.get(coords, None)

    def get_light_sources(self):
        return self._light_sources

    def place_enemy(self, coords: Vec2, enemy: Enemy):
        enemy.move_to(coords)
        self._enemies[coords] = enemy

    def remove_enemy(self, enemy: Enemy):
        coords = enemy.get_coords()
        if coords in self._enemies and self._enemies[coords] == enemy:
            del self._enemies[coords]

    def get_enemy(self, coords: Vec2):
        return self._enemies.get(coords, None)

    def spawn_objects(self):
        for obj_to_spawn in [Chest(), LightSource(3), Heal(), Heal()]:
            ys = list(range(2, self._height-3))
            random.shuffle(ys)
            to_break = False
            for y in ys:
                xs = list(range(int(self._width*0.2), self._width-3))
                random.shuffle(xs)
                for x in xs:
                    (tile_id, _, _), obj, enemy = self.get_all(Vec2(x, y))
                    if tile_id == Tile.id_Floor and obj is None and enemy is None:
                        if random.randint(0, 100) < 10:
                            self.place_object(Vec2(x, y), obj_to_spawn)
                            to_break = True
                            break
                if to_break:
                    break

    def spawn_enemy(self, amount, diff):
        for i in range(amount):
            enemy_to_spawn = Enemy(diff + random.randint(-1, 1))
            ys = list(range(2, self._height-3))
            random.shuffle(ys)
            to_break = False
            for y in ys:
                xs = list(range(int(self._width*0.2), self._width-3))
                random.shuffle(xs)
                for x in xs:
                    (tile_id, _, _), obj, enemy = self.get_all(Vec2(x, y))
                    if tile_id == Tile.id_Floor and obj is None and enemy is None:
                        if random.randint(0, 100) < 10:
                            self.place_enemy(Vec2(x, y), enemy_to_spawn)
                            to_break = True
                            break
                if to_break:
                    break


class LevelGenerator:
    WALL = 1
    UNVISITED = 0
    VISITED = 2

    @staticmethod
    def generate_test_room(width, height):
        lvl = []
        for y in range(height):
            lvl.append([])
            for x in range(width):
                if x == width-1 and y == 8:
                    lvl[y].append(Tile.id_Exit)
                elif x == 0 or y == 0 or x == width-1 or y == height-1:
                    lvl[y].append(Tile.id_Wall)
                elif x == 2 and y == 2:
                    lvl[y].append(Tile.id_PlayerSpawn)
                else:
                    lvl[y].append(Tile.id_Floor)
        level = Level(lvl)
        level.place_object(Vec2(5, 2), LightSource(3))
        level.place_enemy(Vec2(2, 5), Enemy(6))
        level.place_object(Vec2(8, 2), Chest())
        return level

    @staticmethod
    def generate_tutorial_room(width, height):
        lvl = []
        for y in range(height):
            lvl.append([])
            for x in range(width):
                if x == width-1 and y == 9:
                    lvl[y].append(Tile.id_Exit)
                elif x == 0 or y == 0 or x == width-1 or y == height-1 or y == 7 or y == 11:
                    lvl[y].append(Tile.id_Wall)
                elif x == 2 and y == 9:
                    lvl[y].append(Tile.id_PlayerSpawn)
                else:
                    lvl[y].append(Tile.id_Floor)
        level = Level(lvl)
        level.place_enemy(Vec2(30, 9), Enemy(1))
        level.place_object(Vec2(32, 8), LightSource(3))
        level.place_object(Vec2(34, 9), Heal())
        level.place_object(Vec2(49, 9), Chest())
        level.place_object(Vec2(51, 8), LightSource(3))
        return level

    @classmethod
    def destroy_random_walls(cls, raw_lvl, chance):
        for y in range(len(raw_lvl)-1):
            for x in range(len(raw_lvl[0])-1):
                if raw_lvl[y][x] == cls.WALL:
                    if random.randint(0, 100)/100 < chance:
                        raw_lvl[y][x] = cls.VISITED

    @classmethod
    def generate_exit(cls, raw_lvl):
        x = len(raw_lvl[0]) - 1
        while True:
            y = random.randint(1, len(raw_lvl)-1)
            if raw_lvl[y][x-1] == cls.VISITED:
                return Vec2(x, y)

    @classmethod
    def generate_labirinth(cls, width, height, chance_destroy_wall):
        raw_lvl = []
        for y in range((height-2)):
            raw_lvl.append([])
            for x in range((width-2)):
                if x % 2 == 0 and y % 2 == 0:
                    raw_lvl[y].append(cls.UNVISITED)
                else:
                    raw_lvl[y].append(cls.WALL)
        spawn_point_x = 0
        while True:
            spawn_point_y = random.randint(0, len(raw_lvl)-1)
            if spawn_point_y % 2 == 0:
                break

        raw_lvl[spawn_point_y][spawn_point_x] = cls.VISITED
        current = Vec2(spawn_point_x, spawn_point_y)
        stack = []
        while True:
            # создаем дополнительные пути
            neighbor = cls.pick_neighbor(raw_lvl, current, cls.VISITED)
            if neighbor is not None and random.randint(0, 100)/100 < chance_destroy_wall:
                wall_to_remove = neighbor - current
                wall_to_remove /= 2
                wall_to_remove += current
                raw_lvl[wall_to_remove.y][wall_to_remove.x] = cls.VISITED

            # построение лабиринта
            neighbor = cls.pick_neighbor(raw_lvl, current, cls.UNVISITED)
            if neighbor is not None:
                stack.append(current)
                wall_to_remove = neighbor - current
                wall_to_remove /= 2
                wall_to_remove += current
                raw_lvl[wall_to_remove.y][wall_to_remove.x] = cls.VISITED
                raw_lvl[neighbor.y][neighbor.x] = cls.VISITED
                current = neighbor
            else:
                if len(stack) == 0:
                    break
                current = stack.pop()
            if len(stack) == 0:
                break

        exit_coords = cls.generate_exit(raw_lvl)
        cls.destroy_random_walls(raw_lvl, chance_destroy_wall)

        lvl = []
        for y in range(height):
            lvl.append([])
            for x in range(width):
                lvl[y].append(Tile.id_Wall)

        for y, row in enumerate(raw_lvl):
            y += 1
            for x, val in enumerate(row):
                x += 1
                if val == cls.WALL:
                    lvl[y][x] = Tile.id_Wall
                elif val == cls.VISITED:
                    lvl[y][x] = Tile.id_Floor
        lvl[spawn_point_y+1][spawn_point_x+1] = Tile.id_PlayerSpawn
        lvl[exit_coords.y+1][exit_coords.x+1] = Tile.id_Exit
        return Level(lvl)

    @classmethod
    def list_of_neighbors(cls, raw_lvl, current):
        neighbors = []
        for offset in [Vec2(0, 2), Vec2(0, -2), Vec2(2, 0), Vec2(-2, 0)]:
            coords = current + offset
            if 0 <= coords.y < len(raw_lvl) and 0 <= coords.x < len(raw_lvl[0]):
                if raw_lvl[coords.y][coords.x] in (cls.UNVISITED, cls.VISITED):
                    neighbors.append((coords, raw_lvl[coords.y][coords.x]))
        return neighbors

    @classmethod
    def pick_neighbor(cls, raw_lvl, current, neighbor_type):
        neighbors = cls.list_of_neighbors(raw_lvl, current)
        neighbors = list(filter(lambda x: x[1] == neighbor_type, neighbors))
        if len(neighbors) == 0:
            return None
        else:
            return random.choice(neighbors)[0]
