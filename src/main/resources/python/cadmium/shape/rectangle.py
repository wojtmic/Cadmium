from dataclasses import dataclass
from cadmium.location import Location
from cadmium.shape.base import Shape, ShapeError, require_same_world


@dataclass
class Rectangle(Shape):
    corner1: Location
    corner2: Location

    def __post_init__(self):
        require_same_world(self.corner1, self.corner2)
        if not (
                self.corner1.x == self.corner2.x or
                self.corner1.y == self.corner2.y or
                self.corner1.z == self.corner2.z
        ):
            raise ShapeError(
                "Rectangle corners must share at least one axis (x, y, or z) - "
                "got a true 3D diagonal with no flat plane. Use Cuboid instead, "
                "or pick two corners that share a coordinate."
            )

    @property
    def _flat_axis(self) -> str:
        if self.corner1.x == self.corner2.x:
            return "x"
        if self.corner1.y == self.corner2.y:
            return "y"
        return "z"

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
    def area(self) -> float:
        dims = {"x": self.width, "y": self.height, "z": self.depth}
        flat = self._flat_axis
        others = [v for k, v in dims.items() if k != flat]
        return others[0] * others[1]

    def _plane_axes(self):
        flat = self._flat_axis
        return [a for a in ("x", "y", "z") if a != flat]

    def positions(self, sub: float = 1.0) -> list[Location]:
        lo, hi = self.min, self.max
        w = lo.world
        a_axis, b_axis = self._plane_axes()

        a_range = getattr(hi, a_axis) - getattr(lo, a_axis)
        b_range = getattr(hi, b_axis) - getattr(lo, b_axis)
        a_steps = max(1, round(a_range / sub))
        b_steps = max(1, round(b_range / sub))

        result = []
        for i in range(a_steps + 1):
            for j in range(b_steps + 1):
                coords = {"x": lo.x, "y": lo.y, "z": lo.z}
                coords[a_axis] = getattr(lo, a_axis) + a_range * (i / a_steps)
                coords[b_axis] = getattr(lo, b_axis) + b_range * (j / b_steps)
                result.append(Location(coords["x"], coords["y"], coords["z"], lo.yaw, lo.pitch, w))
        return result

    def outline(self, sub: float = 1.0) -> list[Location]:
        from cadmium.shape.line import Line
        lo, hi = self.min, self.max
        w = lo.world
        a_axis, b_axis = self._plane_axes()
        base = {"x": lo.x, "y": lo.y, "z": lo.z}

        def at(a_val, b_val):
            c = dict(base)
            c[a_axis] = a_val
            c[b_axis] = b_val
            return Location(c["x"], c["y"], c["z"], lo.yaw, lo.pitch, w)

        a0, a1 = getattr(lo, a_axis), getattr(hi, a_axis)
        b0, b1 = getattr(lo, b_axis), getattr(hi, b_axis)
        corners = [at(a0, b0), at(a1, b0), at(a1, b1), at(a0, b1)]

        seen = set()
        result = []
        for a, b in zip(corners, corners[1:] + corners[:1]):
            for pos in Line(a, b).positions(sub):
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
        return f"Rectangle({self.corner1}, {self.corner2})"