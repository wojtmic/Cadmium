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

class EVENTS(Enum):
    player_join = "player_join"
    player_quit = "player_quit"
    player_death = "player_death"
    block_break = "block_break"
    block_place = "block_place"
    chat = "chat"


_registry: dict[EVENTS, list] = {}


def on(*events: EVENTS):
    def decorator(func):
        for event in events:
            _registry.setdefault(event, []).append(func)
        return func
    return decorator

_event_classes = {}

def _dispatch(event: EVENTS, raw):
    cls = _event_classes.get(event)
    obj = cls(raw) if cls else Event(raw=raw)
    for handler in _registry.get(event, []):
        handler(obj)
