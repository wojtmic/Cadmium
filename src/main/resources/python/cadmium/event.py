from dataclasses import dataclass, field
from cadmium.player import Player
from cadmium.entity import entity_from_raw
from cadmium.inventory import itemstack_from


def _wrap_player(raw):
    p = raw.getPlayer() if hasattr(raw, 'getPlayer') else None
    return Player(raw=p) if p is not None else None


@dataclass
class Event:
    raw: object
    player: Player = field(default=None, init=False)

    def __post_init__(self):
        self.player = _wrap_player(self.raw)

    def cancel(self):
        self.raw.setCancelled(True)


@dataclass
class EntityDeathEvent:
    raw: object

    @property
    def entity(self):
        return entity_from_raw(self.raw.getEntity())

    @property
    def killer(self):
        killer = self.raw.getEntity().getKiller()
        return entity_from_raw(killer) if killer is not None else None

    @property
    def drops(self) -> list:
        return [itemstack_from(i) for i in self.raw.getDrops()]

    def clear_drops(self):
        self.raw.getDrops().clear()

    def add_drop(self, item):
        self.raw.getDrops().add(item.raw)

    @property
    def dropped_exp(self) -> int:
        return self.raw.getDroppedExp()

    @dropped_exp.setter
    def dropped_exp(self, value: int):
        self.raw.setDroppedExp(value)

    def __repr__(self):
        return f"EntityDeathEvent({self.entity})"


@dataclass
class EntityDamageEvent:
    raw: object

    @property
    def entity(self):
        return entity_from_raw(self.raw.getEntity())

    @property
    def damage(self) -> float:
        return self.raw.getDamage()

    @damage.setter
    def damage(self, value: float):
        self.raw.setDamage(value)

    @property
    def final_damage(self) -> float:
        return self.raw.getFinalDamage()

    @property
    def cause(self):
        return self.raw.getCause()

    @property
    def damager(self):
        if hasattr(self.raw, "getDamager"):
            return entity_from_raw(self.raw.getDamager())
        return None

    def cancel(self):
        self.raw.setCancelled(True)

    def __repr__(self):
        return f"EntityDamageEvent({self.entity}, {self.damage})"


@dataclass
class PlayerInteractEntityEvent:
    raw: object

    @property
    def player(self):
        return Player(raw=self.raw.getPlayer())

    @property
    def entity(self):
        return entity_from_raw(self.raw.getRightClicked())

    def cancel(self):
        self.raw.setCancelled(True)

    def __repr__(self):
        return f"PlayerInteractEntityEvent({self.player}, {self.entity})"