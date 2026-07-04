import java
from datetime import datetime
from cadmium.player import Player

Date = java.type("java.util.Date")

def to_java_date(value):
    if isinstance(value, datetime):
        millis = int(value.timestamp() * 1000)
    elif isinstance(value, (int, float)):
        millis = int(value * 1000)
    else:
        raise TypeError(f"expected datetime or unix seconds, got {type(value)}")
    return Date(millis)

_MiniMessage = java.type("net.kyori.adventure.text.minimessage.MiniMessage")

def mm(text: str):
    return _MiniMessage.miniMessage().deserialize(text)

def mini_message(text: str): return mm(text)

def serialize_mini_message(text: str):
    return _MiniMessage.miniMessage().serialize(text)

def find_player(name: str):
    raw = _Bukkit.getPlayerExact(name)
    if raw is None:
        return None
    return Player(raw=raw)
