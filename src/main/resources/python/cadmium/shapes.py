from dataclasses import dataclass
from cadmium.location import Location


class ShapeError(ValueError):
    pass


class Shape:
    """Common base for Line, Rectangle, Cuboid, etc."""

    def positions(self, sub: float = 1.0) -> list[Location]:
        raise NotImplementedError

    def contains(self, position: Location) -> bool:
        raise NotImplementedError


def _require_same_world(a: Location, b: Location):
    if a.world != b.world:
        raise ShapeError(
            f"positions are in different worlds: {a.world} vs {b.world}"
        )


@dataclass
class Line(Shape):
    start: Location
    end: Location

    def __post_init__(self):
        _require_same_world(self.start, self.end)

    @property
    def length(self) -> float:
        return self.start.distance(self.end)

    def positions(self, sub: float = 1.0) -> list[Location]:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        dz = self.end.z - self.start.z
        distance = self.length

        if distance == 0:
            return [self.start]

        steps = max(1, round(distance / sub))
        return [
            Location(
                self.start.x + dx * (i / steps),
                self.start.y + dy * (i / steps),
                self.start.z + dz * (i / steps),
                self.start.yaw,
                self.start.pitch,
                self.start.world,
                )
            for i in range(steps + 1)
        ]

    def contains(self, position: Location, tolerance: float = 0.01) -> bool:
        if position.world != self.start.world:
            return False
        # point-to-segment distance
        dx, dy, dz = (self.end.x - self.start.x, self.end.y - self.start.y, self.end.z - self.start.z)
        length_sq = dx * dx + dy * dy + dz * dz
        if length_sq == 0:
            return self.start.distance(position) <= tolerance

        t = max(0.0, min(1.0, (
                (position.x - self.start.x) * dx +
                (position.y - self.start.y) * dy +
                (position.z - self.start.z) * dz
        ) / length_sq))

        closest = Location(
            self.start.x + t * dx,
            self.start.y + t * dy,
            self.start.z + t * dz,
            self.start.yaw, self.start.pitch, self.start.world,
            )
        return closest.distance(position) <= tolerance

    def __repr__(self):
        return f"Line({self.start}, {self.end})"