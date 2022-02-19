import random

from color import Color
from vec2 import Vec2


class GameObject:
    def __init__(self):
        self._char = '╳'
        self._color = Color.White
        self._coords = Vec2()

    def get_coords(self):
        return self._coords

    def get_char(self):
        return self._char, self._color

    def move_to(self, coords: Vec2):
        self._coords = coords


class Heal(GameObject):
    def __init__(self):
        super().__init__()
        self._char = '+'
        self._color = Color.Yellow


class LightSource(GameObject):
    def __init__(self, radius):
        super().__init__()
        self._char = 'Ï'
        self._color = Color.Yellow
        self._radius = radius

    def set_radius(self, value):
        self._radius = value

    def get_lighting(self, symbol_aspect):
        r0 = self._radius ** 2
        x_from = -int(self._radius / symbol_aspect)
        x_to = int((self._radius + 1) / symbol_aspect)
        r1 = r0 * 0.8
        r2 = r0 * 0.6
        r3 = r0 * 0.4
        result = []
        tmp = set()
        for y in range(-self._radius, self._radius + 1):
            for x in range(x_from, x_to):
                xi = x * symbol_aspect
                xy = xi**2 + y**2
                if xy < r3:
                    value = 4
                elif xy < r2:
                    value = 3
                elif xy < r1:
                    value = 2
                elif xy < r0:
                    value = 1
                else:
                    value = 0
                x = int(x * 0.95)
                if (x, y) not in tmp:
                    tmp.add((x, y))
                    result.append((Vec2(x, y), value))
        return result


class Chest(GameObject):
    LightLevelUpgrade = 1
    LightsAmountUpgrade = 2
    MaxHPUpgrage = 3
    BattleTimeUpgrade = 4

    def __init__(self):
        super().__init__()
        self._char = '■'
        self._color = Color.Yellow

    @classmethod
    def get_upgrade(cls):
        return random.choice([cls.LightLevelUpgrade, cls.LightsAmountUpgrade, cls.BattleTimeUpgrade, cls.MaxHPUpgrage])


class Enemy(GameObject):
    def __init__(self, difficulty):
        super().__init__()
        self._char = '§'
        self._color = Color.Red

        if difficulty < 0:
            difficulty = 0
        self.dmg = difficulty
        self.difficulty = difficulty

    def get_code_list(self):
        return self._generate_code(self.difficulty)

    def get_difficulty(self):
        return self.difficulty

    def get_dmg(self):
        return self.dmg

    @classmethod
    def _generate_code(cls, difficulty):
        result = []
        result.append(cls._gen_code_block_hack())
        if difficulty >= 10:
            result.append(cls._gen_code_block_10())
        if difficulty >= 9:
            result.append(cls._gen_code_block_9())
        if difficulty >= 8:
            result.append(cls._gen_code_block_8())
        if difficulty >= 7:
            result.append(cls._gen_code_block_7())
        if difficulty >= 6:
            result.append(cls._gen_code_block_6())
        if difficulty >= 5:
            result.append(cls._gen_code_block_5())
        if difficulty >= 4:
            result.append(cls._gen_code_block_4())
        if difficulty >= 3:
            result.append(cls._gen_code_block_3())
        if difficulty >= 2:
            result.append(cls._gen_code_block_2())
        if difficulty >= 1:
            result.append(cls._gen_code_block_1(difficulty))
        result.append(cls._gen_code_block_kill())
        for i in range(len(result)):
            result[i] += '\n'
        return result

    @staticmethod
    def _gen_code_block_hack():
        func_name = random.choice(['hack', 'init_hack', 'startHack'])
        arg = random.choice(['enemy', 'script', 'process', 'defence', ''])
        return f'{func_name}({arg})'

    @staticmethod
    def _gen_code_block_kill():
        func_name = random.choice(['kill', 'finish', 'exit'])
        arg = random.choice(['enemy', 'script', 'process', '', '', ''])
        return f'{func_name}({arg})'

    @staticmethod
    def _gen_code_block_1(diff):
        func_name = random.choice(['password', 'pass', 'enter_pass', 'enter_password', 'EnterPass'])
        a = 'abcdefghijklmnopqrstuvwxyz'
        d = '0123456789'
        s = '!?.#@$%_-&'
        if diff < 3:
            alphabets = [a]
        elif diff < 6:
            alphabets = [a, a.upper()]
        elif diff < 9:
            alphabets = [a, a.upper(), d]
        else:
            alphabets = [a, a.upper(), d, s]
        pwd = ''
        for i in range(diff+2):
            alph = random.choice(alphabets)
            pwd += random.choice(alph)
        return f'{func_name}({pwd})'

    @staticmethod
    def _gen_code_block_2():
        func_name = random.choice(['brute_force', 'BruteForceHack', 'start_brute_force'])
        return f'{func_name}()'

    @staticmethod
    def _gen_code_block_3():
        func_name = random.choice(['CodeInjection', 'InjectCode', 'inject_aob'])
        arg = random.choice(['', 'func', 'aob'])
        return f'{func_name}({arg})'

    @staticmethod
    def _gen_code_block_4():
        func_name = random.choice(['MemScan', 'MemoryScan', 'mem_scan', 'memory_scan'])
        arg = hex(int.from_bytes(random.randbytes(4), 'big'))
        if random.randint(0, 1):
            arg = arg.upper()
        return f'{func_name}({arg})'

    @staticmethod
    def _gen_code_block_5():
        func_name = random.choice(['ForkBomb', 'startForkBomb', 'fork_bomb'])
        arg = str(random.randint(10**4, 10**6))
        return f'{func_name}({arg})'

    @staticmethod
    def _gen_code_block_6():
        func_name = random.choice(['buffer_overflow', 'BufferOverflow', 'InitBufferOF'])
        return f'{func_name}()'

    @staticmethod
    def _gen_code_block_7():
        func_name = random.choice(['InjectSQL', 'SQLInjection', 'StartSQLI'])
        arg = random.choice(['', 'query', 'sql_query'])
        return f'{func_name}({arg})'

    @staticmethod
    def _gen_code_block_8():
        func_name = random.choice(['startMITM', 'ManInTheMiddle', 'MITM', 'HackMITM'])
        return f'{func_name}()'

    @staticmethod
    def _gen_code_block_9():
        func_name = random.choice(['shatter_attack', 'startShatterAttack', 'shatterAtt'])
        return f'{func_name}()'

    @staticmethod
    def _gen_code_block_10():
        func_name = random.choice(['openPorts', 'lookForPort', 'find_open_port'])
        return f'{func_name}()'
