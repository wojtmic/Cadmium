import java
from datetime import datetime

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
