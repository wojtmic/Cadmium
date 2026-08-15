import java

_FastBoard = java.type("fr.mrmicky.fastboard.adventure.FastBoard")

_boards: dict = {}


class _FastboardLines(list):
    def __init__(self, board, lines):
        super().__init__(lines)
        self._board = board

    def _push(self):
        from cadmium.utils import mm
        self._board.updateLines([mm(line) for line in self])

    def _check_len(self):
        if len(self) > 15:
            raise ValueError(f"fastboard supports at most 15 lines, got {len(self)}")

    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self._check_len()
        self._push()

    def __delitem__(self, index):
        super().__delitem__(index)
        self._push()

    def append(self, value):
        super().append(value)
        self._check_len()
        self._push()

    def extend(self, values):
        super().extend(values)
        self._check_len()
        self._push()

    def insert(self, index, value):
        super().insert(index, value)
        self._check_len()
        self._push()

    def remove(self, value):
        super().remove(value)
        self._push()

    def pop(self, index=-1):
        value = super().pop(index)
        self._push()
        return value

    def clear(self):
        super().clear()
        self._push()

    def sort(self, *args, **kwargs):
        super().sort(*args, **kwargs)
        self._push()

    def reverse(self):
        super().reverse()
        self._push()

    def __iadd__(self, other):
        result = super().__iadd__(other)
        self._check_len()
        self._push()
        return result

def _entry(player):
    return _boards.get(player.raw.getUniqueId())

def _get_or_create(player):
    uuid = player.raw.getUniqueId()
    entry = _boards.get(uuid)
    if entry is None:
        entry = [_FastBoard(player.raw), "", None]
        entry[2] = _FastboardLines(entry[0], [])
        _boards[uuid] = entry
    return entry

def _clear(player):
    uuid = player.raw.getUniqueId()
    entry = _boards.pop(uuid, None)
    if entry is not None:
        entry[0].delete()