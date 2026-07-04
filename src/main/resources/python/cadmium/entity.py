from dataclasses import dataclass
import java
from cadmium.location import Location, location_from
from cadmium.data import BlockCustomData

_Bukkit = java.type("org.bukkit.Bukkit")
_UUID = java.type("java.util.UUID")
_Player = java.type("org.bukkit.entity.Player")
_LivingEntity = java.type("org.bukkit.entity.LivingEntity")
_EntityType = java.type("org.bukkit.entity.EntityType")

EntityType = _EntityType

@dataclass
class Entity:
    raw: object

    @property
    def uuid(self):
        return self.raw.getUniqueId()

    @property
    def name(self) -> str:
        return self.raw.getName()

    @property
    def is_valid(self) -> bool:
        return self.raw.isValid()

    @property
    def is_dead(self) -> bool:
        return self.raw.isDead()

    def remove(self):
        self.raw.remove()

    @property
    def location(self) -> Location:
        return location_from(self.raw.getLocation())

    @location.setter
    def location(self, loc: Location):
        self.raw.teleport(loc.raw)

    def teleport(self, loc: Location):
        self.raw.teleport(loc.raw)

    @property
    def world(self):
        return self.raw.getWorld()

    @property
    def velocity(self):
        return self.raw.getVelocity()

    @velocity.setter
    def velocity(self, vec):
        self.raw.setVelocity(vec)

    @property
    def is_on_ground(self) -> bool:
        return self.raw.isOnGround()

    @property
    def is_glowing(self) -> bool:
        return self.raw.isGlowing()

    @is_glowing.setter
    def is_glowing(self, val: bool):
        self.raw.setGlowing(val)

    @property
    def is_silent(self) -> bool:
        return self.raw.isSilent()

    @is_silent.setter
    def is_silent(self, val: bool):
        self.raw.setSilent(val)

    @property
    def gravity(self) -> bool:
        return self.raw.hasGravity()

    @gravity.setter
    def gravity(self, val: bool):
        self.raw.setGravity(val)

    @property
    def custom_name(self) -> str:
        from cadmium.utils import serialize_mini_message
        component = self.raw.customName()
        return serialize_mini_message(component) if component is not None else None

    @custom_name.setter
    def custom_name(self, val: str):
        from cadmium.utils import mm
        self.raw.customName(mm(val) if val is not None else None)

    @property
    def custom_data(self) -> BlockCustomData:
        return BlockCustomData(self.raw)

    def send(self, msg: str):
        from cadmium.utils import mm
        self.raw.sendMessage(mm(msg))

    @property
    def type(self):
        return self.raw.getType()

    def __repr__(self):
        return f"Entity({self.raw.getType()}, {self.uuid})"


def entity_from_raw(raw):
    if raw is None:
        return None
    if isinstance(raw, _Player):
        from cadmium.player import Player
        return Player(raw=raw)
    if isinstance(raw, _LivingEntity):
        from cadmium.living_entity import LivingEntity
        return LivingEntity(raw=raw)
    return Entity(raw=raw)


def entity_from_uuid(uuid):
    if isinstance(uuid, str):
        uuid = _UUID.fromString(uuid)
    raw = _Bukkit.getEntity(uuid)
    return entity_from_raw(raw)


def spawn_entity(location: Location, entity_type):
    raw = location.world.spawnEntity(location.raw, entity_type)
    return entity_from_raw(raw)