import java

_PersistentDataType = java.type("org.bukkit.persistence.PersistentDataType")
_NamespacedKey = java.type("org.bukkit.NamespacedKey")

class PersistentData:
    def __init__(self, raw_holder):
        self._holder = raw_holder

    def _key(self, name: str):
        return _NamespacedKey("cadmium", name)

    def _infer_type(self, value):
        if isinstance(value, bool):
            return _PersistentDataType.BOOLEAN
        if isinstance(value, int):
            return _PersistentDataType.INTEGER
        if isinstance(value, float):
            return _PersistentDataType.DOUBLE
        if isinstance(value, str):
            return _PersistentDataType.STRING
        raise TypeError(f"Unsupported persistent data type: {type(value)}")

    def __setitem__(self, name: str, value):
        pdt = self._infer_type(value)
        self._holder.getPersistentDataContainer().set(self._key(name), pdt, value)

    def __getitem__(self, name: str):
        val = self.get(name)
        if val is None:
            raise KeyError(name)
        return val

    def get(self, name: str, default=None):
        container = self._holder.getPersistentDataContainer()
        key = self._key(name)
        for pdt in (_PersistentDataType.STRING, _PersistentDataType.INTEGER,
                    _PersistentDataType.DOUBLE, _PersistentDataType.BOOLEAN):
            if container.has(key, pdt):
                return container.get(key, pdt)
        return default

    def __contains__(self, name: str):
        container = self._holder.getPersistentDataContainer()
        key = self._key(name)
        return any(container.has(key, pdt) for pdt in (
            _PersistentDataType.STRING, _PersistentDataType.INTEGER,
            _PersistentDataType.DOUBLE, _PersistentDataType.BOOLEAN))

    def __delitem__(self, name: str):
        self._holder.getPersistentDataContainer().remove(self._key(name))