from dataclasses import dataclass
import java

_Vector = java.type("org.bukkit.util.Vector")

@dataclass
class Vector:
    x: float
    y: float
    z: float

    @property
    def raw(self):
        return _Vector(self.x, self.y, self.z)

    @property
    def length(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def normalized(self) -> "Vector":
        length = self.length
        if length == 0:
            return Vector(0.0, 0.0, 0.0)
        return Vector(self.x / length, self.y / length, self.z / length)

    def dot(self, other: "Vector") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"


def vector_from(raw) -> Vector:
    return Vector(x=raw.getX(), y=raw.getY(), z=raw.getZ())