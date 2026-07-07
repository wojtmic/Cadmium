from dataclasses import dataclass, field
from cadmium.player import Player
from cadmium.entity import entity_from_raw
from cadmium.inventory import itemstack_from


def _wrap_player(raw):
    p = raw.getPlayer() if hasattr(raw, 'getPlayer') else None
    return Player(raw=p) if p is not None else None


class _CancellableMixin:
    _cancel_window_closed: bool = False

    def _close_cancel_window(self):
        self._cancel_window_closed = True

    def _guarded_cancel(self):
        if self._cancel_window_closed:
            raise RuntimeError(
                "event.cancel() called after the handler's first await - "
                "this is too late, the underlying event has already been "
                "processed by the server. Call event.cancel() before your "
                "first await, or restructure the handler so the decision "
                "to cancel happens synchronously."
            )
        self.raw.setCancelled(True)


@dataclass
class Event(_CancellableMixin):
    raw: object
    player: Player = field(default=None, init=False)

    def __post_init__(self):
        self.player = _wrap_player(self.raw)
        self._cancel_window_closed = False

    def cancel(self):
        self._guarded_cancel()


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
class EntityDamageEvent(_CancellableMixin):
    raw: object
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

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
        self._guarded_cancel()

    def __repr__(self):
        return f"EntityDamageEvent({self.entity}, {self.damage})"


@dataclass
class PlayerInteractEntityEvent(_CancellableMixin):
    raw: object
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self):
        return Player(raw=self.raw.getPlayer())

    @property
    def entity(self):
        return entity_from_raw(self.raw.getRightClicked())

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerInteractEntityEvent({self.player}, {self.entity})"