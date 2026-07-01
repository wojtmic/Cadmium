from dataclasses import dataclass, field
import java
from cadmium.block import Block

_JLocation = java.type("org.bukkit.Location")

@dataclass
class Location:
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
    world: object = None

    @property
    def raw(self):
        return _JLocation(self.world, self.x, self.y, self.z, self.yaw, self.pitch)

    def distance(self, other: "Location") -> float:
        return self.raw.distance(other.raw)

    @property
    def block(self) -> Block:
        return Block(raw=self.raw.getBlock())

    def above(self, n: float = 1.0) -> "Location":
        return Location(self.x, self.y + n, self.z, self.yaw, self.pitch, self.world)

    def below(self, n: float = 1.0) -> "Location":
        return Location(self.x, self.y - n, self.z, self.yaw, self.pitch, self.world)

    def north(self, n: float = 1.0) -> "Location":
        return Location(self.x, self.y, self.z - n, self.yaw, self.pitch, self.world)

    def south(self, n: float = 1.0) -> "Location":
        return Location(self.x, self.y, self.z + n, self.yaw, self.pitch, self.world)

    def east(self, n: float = 1.0) -> "Location":
        return Location(self.x + n, self.y, self.z, self.yaw, self.pitch, self.world)

    def west(self, n: float = 1.0) -> "Location":
        return Location(self.x - n, self.y, self.z, self.yaw, self.pitch, self.world)

    def __repr__(self):
        return f"Location({self.x}, {self.y}, {self.z})"


def location_from(loc) -> Location:
    return Location(
        x=loc.getX(),
        y=loc.getY(),
        z=loc.getZ(),
        yaw=loc.getYaw(),
        pitch=loc.getPitch(),
        world=loc.getWorld(),
    )