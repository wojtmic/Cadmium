from dataclasses import dataclass, field
from cadmium.player import Player


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
