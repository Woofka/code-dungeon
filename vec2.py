class Vec2:
    def __init__(self, x=0, y=0):
        self._x = 0
        self._y = 0
        self.x = x
        self.y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        if not isinstance(value, int):
            raise ValueError('X should be integer')
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        if not isinstance(value, int):
            raise ValueError('Y should be integer')
        self._y = value

    @classmethod
    def from_vec(cls, other):
        if not isinstance(other, Vec2):
            raise ValueError(f'Can not transform {type(other)} to Vec2')
        return Vec2(other.x, other.y)

    def __add__(self, other):
        if isinstance(other, int):
            other = Vec2(other, other)
        return Vec2(self._x + other.x, self._y + other.y)

    def __sub__(self, other):
        if isinstance(other, int):
            other = Vec2(other, other)
        return Vec2(self._x - other.x, self._y - other.y)

    def __str__(self):
        return f'({self._x}, {self._y})'

    def __floordiv__(self, other):
        if isinstance(other, int):
            other = Vec2(other, other)
        return Vec2(self._x // other.x, self._y // other.y)

    def __truediv__(self, other):
        if isinstance(other, int):
            other = Vec2(other, other)
        return self // other

    def __hash__(self):
        return hash((self._x, self._y))

    def __eq__(self, other):
        return hash(self) == hash(other)
