from dataclasses import dataclass, field
from typing import TYPE_CHECKING
import java

if TYPE_CHECKING:
    from cadmium.world import World

_JLocation = java.type("org.bukkit.Location")

@dataclass
class Location:
    x: float
    y: float
    z: float
    yaw: float = 0.0
    pitch: float = 0.0
    world: "World" = None

    @property
    def raw(self):
        world_raw = self.world.raw if self.world is not None else None
        return _JLocation(world_raw, self.x, self.y, self.z, self.yaw, self.pitch)

    def distance(self, other: "Location") -> float:
        return self.raw.distance(other.raw)

    @property
    def block(self) -> "Block":
        from cadmium.block import Block
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

    def explode(self, power: float = 4.0, set_fire: bool = False, break_blocks: bool = True) -> bool:
        return self.world.raw.createExplosion(self.x, self.y, self.z, power, set_fire, break_blocks)

    def strike_lightning(self, effect_only: bool = False):
        if effect_only:
            return self.world.raw.strikeLightningEffect(self.raw)
        return self.world.raw.strikeLightning(self.raw)

    def __repr__(self):
        return f"Location({self.x}, {self.y}, {self.z})"


def location_from(loc) -> Location:
    from cadmium.world import world_from
    return Location(
        x=loc.getX(),
        y=loc.getY(),
        z=loc.getZ(),
        yaw=loc.getYaw(),
        pitch=loc.getPitch(),
        world=world_from(loc.getWorld()),
    )