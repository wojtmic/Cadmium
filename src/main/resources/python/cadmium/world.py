import java
from dataclasses import dataclass
from collections.abc import MutableMapping

_Bukkit = java.type("org.bukkit.Bukkit")
_GameRule = java.type("org.bukkit.GameRule")


class GameRules(MutableMapping):
    """Dict-like live view over a World's gamerules."""

    def __init__(self, world_raw):
        self._world = world_raw

    def _rule(self, name: str):
        rule = _GameRule.getByName(name)
        if rule is None:
            raise KeyError(name)
        return rule

    def __getitem__(self, name: str):
        return self._world.getGameRuleValue(self._rule(name))

    def __setitem__(self, name: str, value):
        self._world.setGameRule(self._rule(name), value)

    def __delitem__(self, name):
        raise TypeError("gamerules cannot be deleted, only set")

    def __iter__(self):
        return iter(self._world.getGameRules())

    def __len__(self):
        return len(self._world.getGameRules())

    def __repr__(self):
        return f"GameRules({dict(self)!r})"


@dataclass
class World:
    raw: object

    @property
    def name(self) -> str:
        return self.raw.getName()

    @property
    def seed(self) -> int:
        return self.raw.getSeed()

    @property
    def time(self) -> int:
        return self.raw.getTime()

    @time.setter
    def time(self, val: int):
        self.raw.setTime(val)

    @property
    def full_time(self) -> int:
        return self.raw.getFullTime()

    @property
    def difficulty(self):
        return self.raw.getDifficulty()

    @difficulty.setter
    def difficulty(self, val):
        self.raw.setDifficulty(val)

    @property
    def spawn_location(self) -> "Location":
        from cadmium.location import location_from
        return location_from(self.raw.getSpawnLocation())

    @spawn_location.setter
    def spawn_location(self, loc: "Location"):
        self.raw.setSpawnLocation(loc.raw)

    @property
    def players(self) -> list:
        from cadmium.player import Player
        return [Player(raw=p) for p in self.raw.getPlayers()]

    @property
    def entities(self) -> list:
        from cadmium.entity import entity_from_raw
        return [entity_from_raw(e) for e in self.raw.getEntities()]

    def block_at(self, x: int, y: int, z: int):
        from cadmium.block import block_from
        return block_from(self.raw.getBlockAt(x, y, z))

    def location(self, x: float, y: float, z: float, yaw: float = 0.0, pitch: float = 0.0) -> "Location":
        from cadmium.location import Location
        return Location(x, y, z, yaw, pitch, self)

    def spawn(self, loc: "Location", entity_type):
        from cadmium.entity import entity_from_raw
        return entity_from_raw(self.raw.spawnEntity(loc.raw, entity_type))

    @property
    def gamerules(self) -> GameRules:
        return GameRules(self.raw)

    @property
    def custom_data(self):
        from cadmium.data import WorldCustomData
        return WorldCustomData(self.raw)

    def __eq__(self, other):
        if not isinstance(other, World):
            return NotImplemented
        return self.raw.equals(other.raw)

    def __hash__(self):
        return hash(self.raw.getUID().toString())

    def __repr__(self):
        return f"World({self.name})"


def world_from(raw) -> World | None:
    if raw is None:
        return None
    return World(raw=raw)


def get_world(name: str) -> World | None:
    raw = _Bukkit.getWorld(name)
    return world_from(raw)


def get_all_worlds() -> list["World"]:
    return [World(raw=w) for w in _Bukkit.getWorlds()]