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
}

def _dispatch(event: EVENTS, raw):
    cls = _event_classes.get(event)
    obj = cls(raw) if cls else Event(raw=raw)
    for handler in _registry.get(event, []):
        handler(obj)
