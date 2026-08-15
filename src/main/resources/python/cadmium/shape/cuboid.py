from dataclasses import dataclass
from cadmium.location import Location
from cadmium.shape.base import Shape, require_same_world


@dataclass
class Cuboid(Shape):
    corner1: Location
    corner2: Location

    def __post_init__(self):
        require_same_world(self.corner1, self.corner2)

    @property
    def min(self) -> Location:
        return Location(
            min(self.corner1.x, self.corner2.x),
            min(self.corner1.y, self.corner2.y),
            min(self.corner1.z, self.corner2.z),
            self.corner1.yaw, self.corner1.pitch, self.corner1.world,
        )

    @property
    def max(self) -> Location:
        return Location(
            max(self.corner1.x, self.corner2.x),
            max(self.corner1.y, self.corner2.y),
            max(self.corner1.z, self.corner2.z),
            self.corner1.yaw, self.corner1.pitch, self.corner1.world,
        )

    @property
    def width(self) -> float:
        return abs(self.corner2.x - self.corner1.x)

    @property
    def height(self) -> float:
        return abs(self.corner2.y - self.corner1.y)

    @property
    def depth(self) -> float:
        return abs(self.corner2.z - self.corner1.z)

    @property
    def volume(self) -> float:
        return self.width * self.height * self.depth

    def positions(self, sub: float = 1.0) -> list[Location]:
        """All positions filling the solid volume of the cuboid."""
        lo, hi = self.min, self.max
        w = lo.world

        x_steps = max(1, round(self.width / sub)) if self.width else 0
        y_steps = max(1, round(self.height / sub)) if self.height else 0
        z_steps = max(1, round(self.depth / sub)) if self.depth else 0

        result = []
        for i in range(x_steps + 1):
            x = lo.x + self.width * (i / x_steps) if x_steps else lo.x
            for j in range(y_steps + 1):
                y = lo.y + self.height * (j / y_steps) if y_steps else lo.y
                for k in range(z_steps + 1):
                    z = lo.z + self.depth * (k / z_steps) if z_steps else lo.z
                    result.append(Location(x, y, z, lo.yaw, lo.pitch, w))
        return result

    def interior(self, sub: float = 1.0) -> list[Location]:
        """Positions strictly inside the cuboid, excluding the outer shell."""
        lo, hi = self.min, self.max
        w = lo.world

        x_steps = max(1, round(self.width / sub)) if self.width else 0
        y_steps = max(1, round(self.height / sub)) if self.height else 0
        z_steps = max(1, round(self.depth / sub)) if self.depth else 0

        result = []
        for i in range(1, x_steps):
            x = lo.x + self.width * (i / x_steps) if x_steps else lo.x
            for j in range(1, y_steps):
                y = lo.y + self.height * (j / y_steps) if y_steps else lo.y
                for k in range(1, z_steps):
                    z = lo.z + self.depth * (k / z_steps) if z_steps else lo.z
                    result.append(Location(x, y, z, lo.yaw, lo.pitch, w))
        return result

    def outline(self, sub: float = 1.0) -> list[Location]:
        """Positions on the 6 faces of the cuboid (the hollow shell)."""
        from cadmium.shape.rectangle import Rectangle
        lo, hi = self.min, self.max
        w = lo.world

        corners = {
            "000": Location(lo.x, lo.y, lo.z, lo.yaw, lo.pitch, w),
            "100": Location(hi.x, lo.y, lo.z, lo.yaw, lo.pitch, w),
            "010": Location(lo.x, hi.y, lo.z, lo.yaw, lo.pitch, w),
            "001": Location(lo.x, lo.y, hi.z, lo.yaw, lo.pitch, w),
            "110": Location(hi.x, hi.y, lo.z, lo.yaw, lo.pitch, w),
            "101": Location(hi.x, lo.y, hi.z, lo.yaw, lo.pitch, w),
            "011": Location(lo.x, hi.y, hi.z, lo.yaw, lo.pitch, w),
            "111": Location(hi.x, hi.y, hi.z, lo.yaw, lo.pitch, w),
        }
        faces = [
            (corners["000"], corners["101"]),  # bottom
            (corners["010"], corners["111"]),  # top
            (corners["000"], corners["011"]),  # -x side
            (corners["100"], corners["111"]),  # +x side
            (corners["000"], corners["110"]),  # -z side
            (corners["001"], corners["111"]),  # +z side
        ]

        seen = set()
        result = []
        for a, b in faces:
            for pos in Rectangle(a, b).positions(sub):
                key = (round(pos.x, 4), round(pos.y, 4), round(pos.z, 4))
                if key not in seen:
                    seen.add(key)
                    result.append(pos)
        return result

    def contains(self, position: Location, tolerance: float = 0.01) -> bool:
        if position.world != self.corner1.world:
            return False
        lo, hi = self.min, self.max
        return (
                lo.x - tolerance <= position.x <= hi.x + tolerance and
                lo.y - tolerance <= position.y <= hi.y + tolerance and
                lo.z - tolerance <= position.z <= hi.z + tolerance
        )

    def __repr__(self):
        return f"Cuboid({self.corner1}, {self.corner2})"