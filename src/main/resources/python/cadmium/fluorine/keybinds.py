import java
from cadmium.aio import wait_ticks

_Bukkit = java.type("org.bukkit.Bukkit")

_CHANNEL = "fluorine:keybinds_register"
_SEND_CHANNEL = "fluorine:keybinds_send"
_handlers: dict = {}

def _encode_string(s: str) -> bytes:
    data = s.encode("utf-8")
    length = len(data)
    out = bytearray()
    while True:
        b = length & 0x7F
        length >>= 7
        if length:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    out.extend(data)
    return bytes(out)

def _decode_string(raw: bytes, pos: int) -> tuple[str, int]:
    length = 0
    shift = 0
    while True:
        b = raw[pos]
        pos += 1
        length |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return bytes(raw[pos:pos + length]).decode("utf-8"), pos + length

def _encode_register(id: str, translation_key: str, default_key: str, category: str) -> bytes:
    out = bytearray()
    out.extend(_encode_string(id))
    out.extend(_encode_string(translation_key))
    out.extend(_encode_string(default_key))
    out.extend(_encode_string(category))
    return bytes(out)

def _decode_send(raw: bytes) -> tuple[str, bool]:
    id, pos = _decode_string(raw, 0)
    pressed = raw[pos] != 0
    return id, pressed

def _on_send_message(channel, player, raw_bytes):
    id, pressed = _decode_send(raw_bytes)
    handler = _handlers.get(id)
    if handler is not None:
        handler(player, pressed)

def _register_channels():
    messenger = _Bukkit.getMessenger()
    if not messenger.isOutgoingChannelRegistered(_plugin, _CHANNEL):
        messenger.registerOutgoingPluginChannel(_plugin, _CHANNEL)
    if not messenger.isIncomingChannelRegistered(_plugin, _SEND_CHANNEL):
        messenger.registerIncomingPluginChannel(_plugin, _SEND_CHANNEL, _on_send_message)

_register_channels()

def register_keybind(player, id: str, translation_key: str, default_key: str, category: str):
    player.raw.sendPluginMessage(_plugin, _CHANNEL, _encode_register(id, translation_key, default_key, category))

def on_keybind(id: str):
    def decorator(func):
        _handlers[id] = func
        return func
    return decorator