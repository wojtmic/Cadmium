from dataclasses import dataclass
import java

_JAttributeModifier = java.type("org.bukkit.attribute.AttributeModifier")
_AttributeModifierOperation = java.type("org.bukkit.attribute.AttributeModifier$Operation")
_EquipmentSlotGroup = java.type("org.bukkit.inventory.EquipmentSlotGroup")
_NamespacedKey = java.type("org.bukkit.NamespacedKey")
Attribute = java.type("org.bukkit.attribute.Attribute")


Attributes = Attribute

Slots = _EquipmentSlotGroup

class AttributeOperations:
    ADD = _AttributeModifierOperation.ADD_NUMBER
    MULTIPLY_BASE = _AttributeModifierOperation.ADD_SCALAR
    MULTIPLY_TOTAL = _AttributeModifierOperation.MULTIPLY_SCALAR_1


@dataclass
class AttributeModifier:
    attribute: object
    slot: object = _EquipmentSlotGroup.ANY
    operation: object = AttributeOperations.ADD
    value: float = 0.0

    def _to_raw(self, name: str):
        key = _NamespacedKey("cadmium", name)
        return _JAttributeModifier(key, self.value, self.operation, self.slot)


class ItemAttributeModifiers:
    def __init__(self, item_stack):
        self._item = item_stack

    def __setitem__(self, name: str, modifier: AttributeModifier):
        meta = self._item.raw.getItemMeta()
        raw_mod = modifier._to_raw(name)
        existing = meta.getAttributeModifiers()
        if existing is not None:
            for attr, mods in list(existing.asMap().items()):
                for m in list(mods):
                    if str(m.getKey().getKey()) == name:
                        meta.removeAttributeModifier(attr, m)
        meta.addAttributeModifier(modifier.attribute, raw_mod)
        self._item.raw.setItemMeta(meta)

    def __getitem__(self, name: str):
        val = self.get(name)
        if val is None:
            raise KeyError(name)
        return val

    def get(self, name: str, default=None):
        meta = self._item.raw.getItemMeta()
        if meta is None or not meta.hasAttributeModifiers():
            return default
        for attr, mods in meta.getAttributeModifiers().asMap().items():
            for m in mods:
                if str(m.getKey().getKey()) == name:
                    return AttributeModifier(
                        attribute=attr,
                        slot=m.getSlotGroup(),
                        operation=m.getOperation(),
                        value=m.getAmount(),
                    )
        return default

    def __delitem__(self, name: str):
        meta = self._item.raw.getItemMeta()
        if meta is None or not meta.hasAttributeModifiers():
            return
        for attr, mods in list(meta.getAttributeModifiers().asMap().items()):
            for m in list(mods):
                if str(m.getKey().getKey()) == name:
                    meta.removeAttributeModifier(attr, m)
        self._item.raw.setItemMeta(meta)

    def __contains__(self, name: str):
        return self.get(name) is not None

    def __repr__(self):
        return f"ItemAttributeModifiers({self._item})"