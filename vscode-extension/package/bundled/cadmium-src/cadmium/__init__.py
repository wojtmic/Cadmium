from enum import Enum
from cadmium.event import *
from cadmium.player import *
from cadmium.command import *
from cadmium.location import *
from cadmium.block import *
from cadmium.data import *
from cadmium.utils import *
from cadmium.inventory import *
from cadmium.schedule import *
from cadmium.event import *
from cadmium.entity import *
from cadmium.living_entity import *
from cadmium.virtual_inventory import *
from cadmium._async import is_async_callable
from cadmium.vector import *
from cadmium.server import *
import builtins

class EVENTS(Enum):
    player_join = "player_join"
    player_quit = "player_quit"
    player_death = "player_death"
    block_break = "block_break"
    block_place = "block_place"
    chat = "chat"
    entity_death = "entity_death"
    entity_damage = "entity_damage"
    player_interact_entity = "player_interact_entity"
    entity_knockback = "entity_knockback"
    entity_pushed_by_entity_attack = "entity_pushed_by_entity_attack"
    player_move = "player_move"

_registry: dict[EVENTS, list] = {}


def on(*events: EVENTS):
    def decorator(func):
        for event in events:
            _registry.setdefault(event, []).append(func)
        return func
    return decorator

_event_classes = {
    EVENTS.entity_death: EntityDeathEvent,
    EVENTS.entity_damage: EntityDamageEvent,
    EVENTS.player_interact_entity: PlayerInteractEntityEvent,
    EVENTS.entity_knockback: EntityKnockbackEvent,
    EVENTS.entity_pushed_by_entity_attack: EntityPushedByEntityAttackEvent,
    EVENTS.chat: ChatEvent,
    EVENTS.player_move: PlayerMoveEvent,
}

def _has_coroutine_manager():
    return hasattr(builtins, "_coroutine_manager")

def _dispatch(event: EVENTS, raw):
    cls = _event_classes.get(event)
    obj = cls(raw) if cls else Event(raw=raw)

    if _has_coroutine_manager():
        _coroutine_manager.notify_event(event.value, obj)

    for handler in _registry.get(event, []):
        if is_async_callable(handler):
            if not _has_coroutine_manager():
                raise RuntimeError(
                    f"async handler {handler!r} registered but no coroutine "
                    "manager is available - this is a Cadmium internal error"
                )
            near = getattr(obj.player, "raw", None) if getattr(obj, "player", None) else None
            _coroutine_manager.start(handler, obj, near)
        else:
            handler(obj)