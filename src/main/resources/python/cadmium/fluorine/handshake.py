import java
import threading
from cadmium.aio import wait_ticks

_Bukkit = java.type("org.bukkit.Bukkit")

_CHANNEL = "fluorine:handshake"
_pending: dict = {}
_results: dict = {}

def _on_message(channel, player, raw_bytes):
    _results[player.getUniqueId()] = _decode_payload(raw_bytes)

def _encode_payload(s: str) -> bytes:
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

def _decode_payload(raw: bytes) -> str:
    pos = 0
    length = 0
    shift = 0
    while True:
        b = raw[pos]
        pos += 1
        length |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return bytes(raw[pos:pos + length]).decode("utf-8")

def _register_channel():
    messenger = _Bukkit.getMessenger()
    if not messenger.isOutgoingChannelRegistered(_plugin, _CHANNEL):
        messenger.registerOutgoingPluginChannel(_plugin, _CHANNEL)
    if not messenger.isIncomingChannelRegistered(_plugin, _CHANNEL):
        messenger.registerIncomingPluginChannel(_plugin, _CHANNEL, _on_message)

_register_channel()
async def check_fluorine(player, server_id: str, timeout: int = 1000) -> str | None:
    uid = player.raw.getUniqueId()
    _results.pop(uid, None)
    player.raw.sendPluginMessage(_plugin, _CHANNEL, _encode_payload(server_id))

    step_ticks = 1
    waited_ms = 0
    while waited_ms < timeout:
        if uid in _results:
            return _results.pop(uid)
        await wait_ticks(step_ticks, near=player.raw)
        waited_ms += step_ticks * 50

    return _results.pop(uid, None)
