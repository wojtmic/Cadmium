import java

_FastBoard = java.type("fr.mrmicky.fastboard.adventure.FastBoard")
_boards: dict = {}


def _entry(player):
    return _boards.get(player.raw.getUniqueId())

def _get_or_create(player):
    uuid = player.raw.getUniqueId()
    entry = _boards.get(uuid)
    if entry is None:
        entry = [_FastBoard(player.raw), "", []]
        _boards[uuid] = entry
    return entry

def _clear(player):
    uuid = player.raw.getUniqueId()
    entry = _boards.pop(uuid, None)
    if entry is not None:
        entry[0].delete()