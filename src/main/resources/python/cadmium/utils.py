import java
from datetime import datetime
from cadmium.entity import entity_from_raw

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

def get_all_entities_of_type(entity_type=None) -> list:
    _Bukkit = java.type("org.bukkit.Bukkit")
    results = []
    for world in _Bukkit.getWorlds():
        for raw in world.getEntities():
            if entity_type is None or raw.getType() == entity_type:
                results.append(entity_from_raw(raw))
    return results

def get_all_entities() -> list:
    return get_all_entities_of_type(None)
