from cadmium.location import Location


class ShapeError(ValueError):
    pass


def require_same_world(a: Location, b: Location):
    if a.world != b.world:
        raise ShapeError(
            f"positions are in different worlds: {a.world} vs {b.world}"
        )


class Shape:
    """Common base for Line, Rectangle, Cuboid, etc."""

    def positions(self, sub: float = 1.0) -> list[Location]:
        raise NotImplementedError

    def contains(self, position: Location) -> bool:
        raise NotImplementedError