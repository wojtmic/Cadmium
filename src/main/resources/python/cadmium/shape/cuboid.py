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

    def outline(self, sub: float = 1.0) -> list[Location]:
        """The 12 edges of the cuboid (true wireframe)."""
        from cadmium.shape.line import Line
        lo, hi = self.min, self.max
        w = lo.world

        c = {
            "000": Location(lo.x, lo.y, lo.z, lo.yaw, lo.pitch, w),
            "100": Location(hi.x, lo.y, lo.z, lo.yaw, lo.pitch, w),
            "010": Location(lo.x, hi.y, lo.z, lo.yaw, lo.pitch, w),
            "001": Location(lo.x, lo.y, hi.z, lo.yaw, lo.pitch, w),
            "110": Location(hi.x, hi.y, lo.z, lo.yaw, lo.pitch, w),
            "101": Location(hi.x, lo.y, hi.z, lo.yaw, lo.pitch, w),
            "011": Location(lo.x, hi.y, hi.z, lo.yaw, lo.pitch, w),
            "111": Location(hi.x, hi.y, hi.z, lo.yaw, lo.pitch, w),
        }
        edges = [
            ("000", "100"), ("100", "110"), ("110", "010"), ("010", "000"),  # bottom face
            ("001", "101"), ("101", "111"), ("111", "011"), ("011", "001"),  # top face
            ("000", "001"), ("100", "101"), ("110", "111"), ("010", "011"),  # verticals
        ]

        seen = set()
        result = []
        for a_key, b_key in edges:
            for pos in Line(c[a_key], c[b_key]).positions(sub):
                key = (round(pos.x, 4), round(pos.y, 4), round(pos.z, 4))
                if key not in seen:
                    seen.add(key)
                    result.append(pos)
        return result

    def positions(self, sub: float = 1.0) -> list[Location]:
        """Positions on the 6 faces of the cuboid (the hollow shell)."""
        from cadmium.shape.rectangle import Rectangle
        lo, hi = self.min, self.max
        w = lo.world

        c = {
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
            (c["000"], c["101"]),  # bottom
            (c["010"], c["111"]),  # top
            (c["000"], c["011"]),  # -x side
            (c["100"], c["111"]),  # +x side
            (c["000"], c["110"]),  # -z side
            (c["001"], c["111"]),  # +z side
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

    def contains(self, position: Location, tolerance: float = 0.01) -> bool:
        if position.world != self.corner1.world:
            return False
        lo, hi = self.min, self.max
        return (
                lo.x - tolerance <= position.x <= hi.x + tolerance and
                lo.y - tolerance <= position.y <= hi.y + tolerance and
                lo.z - tolerance <= position.z <= hi.z + tolerance
        )

    def entities(self) -> list:
        import java
        from cadmium.entity import entity_from_raw

        _BoundingBox = java.type("org.bukkit.util.BoundingBox")
        lo, hi = self.min, self.max
        box = _BoundingBox(lo.x, lo.y, lo.z, hi.x, hi.y, hi.z)
        return [entity_from_raw(e) for e in self.corner1.world.raw.getNearbyEntities(box)]

    def __repr__(self):
        return f"Cuboid({self.corner1}, {self.corner2})"