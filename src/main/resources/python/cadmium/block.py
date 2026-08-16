from dataclasses import dataclass
from cadmium.data import BlockCustomData
import java

Material = java.type("org.bukkit.Material")
_Lightable = java.type("org.bukkit.block.data.Lightable")

@dataclass
class Block:
    raw: object

    @property
    def location(self) -> "Location":
        from cadmium.location import location_from
        return location_from(self.raw.getLocation())

    @property
    def type(self):
        return self.raw.getType()

    @type.setter
    def type(self, material):
        self.raw.setType(material)

    @property
    def material(self):
        return self.raw.getType()

    @material.setter
    def material(self, material):
        self.raw.setType(material)

    @property
    def block_data(self):
        return self.raw.getBlockData()

    @block_data.setter
    def block_data(self, data):
        self.raw.setBlockData(data)

    @property
    def x(self) -> int:
        return self.raw.getX()

    @property
    def y(self) -> int:
        return self.raw.getY()

    @property
    def z(self) -> int:
        return self.raw.getZ()

    @property
    def world(self):
        from cadmium.world import world_from
        return world_from(self.raw.getWorld())

    @property
    def custom_data(self) -> BlockCustomData:
        return BlockCustomData(self.raw)

    def break_naturally(self) -> bool:
        return self.raw.breakNaturally()

    def is_empty(self) -> bool:
        return self.raw.isEmpty()

    def is_liquid(self) -> bool:
        return self.raw.isLiquid()

    def is_solid(self) -> bool:
        return self.raw.isSolid()

    def get_relative(self, dx: int, dy: int, dz: int) -> "Block":
        return Block(raw=self.raw.getRelative(dx, dy, dz))

    @property
    def lit(self) -> bool:
        data = self.raw.getBlockData()
        if not isinstance(data, _Lightable):
            return None
        return data.isLit()

    @lit.setter
    def lit(self, val: bool):
        data = self.raw.getBlockData()
        if not isinstance(data, _Lightable):
            raise TypeError(f"{self.type} is not Lightable")
        data.setLit(val)
        self.raw.setBlockData(data)

    def __repr__(self):
        return f"Block({self.type}, {self.x}, {self.y}, {self.z})"

def block_from(raw) -> Block | None:
    if raw is None:
        return None
    return Block(raw=raw)
