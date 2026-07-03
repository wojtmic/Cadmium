from dataclasses import dataclass
from cadmium.data import BlockCustomData
import java

Material = java.type("org.bukkit.Material")

@dataclass
class Block:
    raw: object

    @property
    def location(self) -> "Location":
        return location_from(self.raw.getLocation())

    @property
    def type(self):
        return self.raw.getType()

    @type.setter
    def type(self, material):
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
        return self.raw.getWorld()

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

    def __repr__(self):
        return f"Block({self.type}, {self.x}, {self.y}, {self.z})"