import java

_PersistentDataType = java.type("org.bukkit.persistence.PersistentDataType")
_NamespacedKey = java.type("org.bukkit.NamespacedKey")

_TYPES_IN_CHECK_ORDER = None


def _types():
    global _TYPES_IN_CHECK_ORDER
    if _TYPES_IN_CHECK_ORDER is None:
        _TYPES_IN_CHECK_ORDER = (
            _PersistentDataType.STRING,
            _PersistentDataType.INTEGER,
            _PersistentDataType.DOUBLE,
            _PersistentDataType.BOOLEAN,
        )
    return _TYPES_IN_CHECK_ORDER


def _infer_type(value):
    if isinstance(value, bool):
        return _PersistentDataType.BOOLEAN
    if isinstance(value, int):
        return _PersistentDataType.INTEGER
    if isinstance(value, float):
        return _PersistentDataType.DOUBLE
    if isinstance(value, str):
        return _PersistentDataType.STRING
    raise TypeError(f"Unsupported persistent data type: {type(value)}")


def _key(name: str):
    return _NamespacedKey("cadmium", name)


class BlockCustomData:
    def __init__(self, raw_holder):
        self._holder = raw_holder

    def __setitem__(self, name: str, value):
        pdt = _infer_type(value)
        self._holder.getPersistentDataContainer().set(_key(name), pdt, value)

    def __getitem__(self, name: str):
        val = self.get(name)
        if val is None:
            raise KeyError(name)
        return val

    def get(self, name: str, default=None):
        container = self._holder.getPersistentDataContainer()
        key = _key(name)
        for pdt in _types():
            if container.has(key, pdt):
                return container.get(key, pdt)
        return default

    def __contains__(self, name: str):
        container = self._holder.getPersistentDataContainer()
        key = _key(name)
        return any(container.has(key, pdt) for pdt in _types())

    def __delitem__(self, name: str):
        self._holder.getPersistentDataContainer().remove(_key(name))

    def __repr__(self):
        return f"BlockCustomData({self._holder})"


class ItemCustomData:
    def __init__(self, item_stack):
        self._item = item_stack

    def __setitem__(self, name: str, value):
        pdt = _infer_type(value)
        meta = self._item.raw.getItemMeta()
        meta.getPersistentDataContainer().set(_key(name), pdt, value)
        self._item.raw.setItemMeta(meta)

    def __getitem__(self, name: str):
        val = self.get(name)
        if val is None:
            raise KeyError(name)
        return val

    def get(self, name: str, default=None):
        meta = self._item.raw.getItemMeta()
        if meta is None:
            return default
        container = meta.getPersistentDataContainer()
        key = _key(name)
        for pdt in _types():
            if container.has(key, pdt):
                return container.get(key, pdt)
        return default

    def __contains__(self, name: str):
        meta = self._item.raw.getItemMeta()
        if meta is None:
            return False
        container = meta.getPersistentDataContainer()
        key = _key(name)
        return any(container.has(key, pdt) for pdt in _types())

    def __delitem__(self, name: str):
        meta = self._item.raw.getItemMeta()
        meta.getPersistentDataContainer().remove(_key(name))
        self._item.raw.setItemMeta(meta)

    def __repr__(self):
        return f"ItemCustomData({self._item})"