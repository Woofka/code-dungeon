from game_object import GameObject, LightSource, Chest
from color import Color
from vec2 import Vec2


class Player(GameObject):
    def __init__(self):
        super().__init__()
        self._char = '@'
        self._color = Color.Green
        self.move_delay = 0.05
        self.next_move = 0

        self._basic_light_radius = 3
        self._max_light_radius = 10
        self.light_level = 1
        self.light_source = LightSource(self.light_radius)
        self.max_lights_limit = 5
        self.max_lights = 1
        self.lights = self.max_lights

        self.max_hp_upgrade_value = 25
        self.max_hp_limit = 250
        self.max_hp = 50
        self.hp = self.max_hp
        self.heal_hp = 0.1

        self.max_time_limit = 60
        self.time_limit_upgrade_value = 5
        self.time_limit = 15
        self.time_left = self.time_limit

        self._score = 0

    def move_to(self, coords: Vec2):
        super().move_to(coords)
        self.light_source.move_to(coords)

    @property
    def basic_light_radius(self):
        return self._basic_light_radius

    @property
    def light_radius(self):
        return self.light_level + self.basic_light_radius

    def upgrade_light_level(self):
        if self.light_radius == self._max_light_radius:
            return False
        self.light_level += 1
        return True

    def get_light_level(self):
        return self.light_level

    def add_light(self):
        self.lights += 1

    def get_lights_count(self):
        return self.lights

    def get_max_lights_count(self):
        return self.max_lights

    def remove_light(self):
        if self.lights > 0:
            self.lights -= 1
            return True
        return False

    def restore_all_lights(self):
        self.lights = self.max_lights

    def upgrade_lights_amount(self):
        if self.max_lights == self.max_lights_limit:
            return False
        self.max_lights += 1
        if self.lights < self.max_lights:
            self.lights += 1
        return True

    def upgrade_hp(self):
        if self.max_hp == self.max_hp_limit:
            return False
        ratio = self.hp / self.max_hp
        self.max_hp += 25
        if self.max_hp > self.max_hp_limit:
            self.max_hp = self.max_hp_limit
        self.hp = self.max_hp * ratio
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        return True

    def get_max_hp(self):
        return self.max_hp

    def get_hp(self):
        return self.hp

    def take_dmg(self, dmg):
        if self.hp < dmg:
            self.hp = 0
        else:
            self.hp -= dmg

    def heal(self):
        self.hp += self.max_hp * self.heal_hp
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def reset_time_left(self):
        self.time_left = self.time_limit

    def get_time_left(self):
        return self.time_left

    def get_time_limit(self):
        return self.time_limit

    def reduce_time_left(self, value):
        self.time_left -= value
        if self.time_left < 0:
            self.time_left = 0

    def upgrade_time_limit(self):
        if self.time_limit == self.max_time_limit:
            return False
        self.time_limit += self.time_limit_upgrade_value
        if self.time_limit > self.max_time_limit:
            self.time_limit = self.max_time_limit
        return True

    def apply_upgrade(self, upgrade):
        if upgrade == Chest.LightLevelUpgrade:
            return self.upgrade_light_level()
        elif upgrade == Chest.LightsAmountUpgrade:
            return self.upgrade_lights_amount()
        elif upgrade == Chest.MaxHPUpgrage:
            return self.upgrade_hp()
        elif upgrade == Chest.BattleTimeUpgrade:
            return self.upgrade_time_limit()

    def add_score(self, value):
        self._score += value

    def get_score(self):
        return self._score
