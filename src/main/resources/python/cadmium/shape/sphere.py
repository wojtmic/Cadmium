import math
from dataclasses import dataclass
from cadmium.location import Location
from cadmium.shape.base import Shape


@dataclass
class Sphere(Shape):
    center: Location
    radius: float

    def __post_init__(self):
        if self.radius <= 0:
            raise ValueError("radius must be > 0")

    @property
    def volume(self) -> float:
        return (4 / 3) * math.pi * self.radius ** 3

    @property
    def surface_area(self) -> float:
        return 4 * math.pi * self.radius ** 2

    def outline(self, sub: float = 1.0) -> list[Location]:
        """Points on the sphere's surface, roughly `sub` blocks apart."""
        c = self.center
        w = c.world

        # approximate point count for the given spacing via surface area
        count = max(1, round(self.surface_area / (sub ** 2)))

        result = []
        golden_angle = math.pi * (3 - math.sqrt(5))
        for i in range(count):
            y = 1 - (i / (count - 1)) * 2 if count > 1 else 0
            r = math.sqrt(max(0, 1 - y * y))
            theta = golden_angle * i

            x = math.cos(theta) * r
            z = math.sin(theta) * r

            result.append(Location(
                c.x + x * self.radius,
                c.y + y * self.radius,
                c.z + z * self.radius,
                c.yaw, c.pitch, w,
                ))
        return result

    def positions(self, sub: float = 1.0) -> list[Location]:
        """All points filling the solid ball."""
        c = self.center
        w = c.world
        r = self.radius

        steps = max(1, round((2 * r) / sub))
        result = []
        for i in range(steps + 1):
            x = -r + (2 * r) * (i / steps)
            for j in range(steps + 1):
                y = -r + (2 * r) * (j / steps)
                for k in range(steps + 1):
                    z = -r + (2 * r) * (k / steps)
                    if x * x + y * y + z * z <= r * r:
                        result.append(Location(c.x + x, c.y + y, c.z + z, c.yaw, c.pitch, w))
        return result

    def contains(self, position: Location, tolerance: float = 0.01) -> bool:
        if position.world != self.center.world:
            return False
        dx = position.x - self.center.x
        dy = position.y - self.center.y
        dz = position.z - self.center.z
        return (dx * dx + dy * dy + dz * dz) <= (self.radius + tolerance) ** 2

    def __repr__(self):
        return f"Sphere({self.center}, r={self.radius})"