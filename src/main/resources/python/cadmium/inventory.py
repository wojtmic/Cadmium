from dataclasses import dataclass, field
import java
from cadmium.utils import mm, serialize_mini_message
from cadmium.data import ItemCustomData

Material = java.type("org.bukkit.Material")
_ItemStack = java.type("org.bukkit.inventory.ItemStack")
_Bukkit = java.type("org.bukkit.Bukkit")
_Enchantment = java.type("org.bukkit.enchantments.Enchantment")
_NamespacedKey = java.type("org.bukkit.NamespacedKey")
_DataComponentType = java.type("io.papermc.paper.datacomponent.DataComponentType")
_DataComponentTypes = java.type("io.papermc.paper.datacomponent.DataComponentTypes")

ItemComponent = _DataComponentTypes

class ComponentMap:
    def __init__(self, item_stack):
        self._item = item_stack

    def __setitem__(self, component_type, value):
        self._item.raw.setData(component_type, value)

    def __getitem__(self, component_type):
        if not self._item.raw.hasData(component_type):
            raise KeyError(component_type)
        return self._item.raw.getData(component_type)

    def get(self, component_type, default=None):
        if self._item.raw.hasData(component_type):
            return self._item.raw.getData(component_type)
        return default

    def __contains__(self, component_type):
        return self._item.raw.hasData(component_type)

    def __delitem__(self, component_type):
        self._item.raw.unsetData(component_type)

    def __repr__(self):
        return f"ComponentMap({self._item})"

def _resolve_enchantment(key):
    if isinstance(key, str):
        ench = _Enchantment.getByKey(_NamespacedKey.minecraft(key.lower()))
        if ench is None:
            raise KeyError(f"Unknown enchantment: {key}")
        return ench
    return key


@dataclass
class ItemStack:
    material: object
    amount: int = 1
    display_name: str = None
    lore: list = field(default_factory=list)
    _raw: object = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if self._raw is not None:
            return
        item = _ItemStack(self.material, self.amount)
        if self.display_name is not None or self.lore:
            meta = item.getItemMeta()
            if self.display_name is not None:
                meta.displayName(mm(self.display_name))
            if self.lore:
                meta.lore([mm(line) for line in self.lore])
            item.setItemMeta(meta)
        self._raw = item

    @property
    def raw(self):
        return self._raw

    @property
    def enchantments(self) -> dict:
        return {str(k.getKey().getKey()): v for k, v in self.raw.getEnchantments().items()}

    @enchantments.setter
    def enchantments(self, value: dict):
        for e in list(self.raw.getEnchantments().keySet()):
            self.raw.removeEnchantment(e)
        for name, level in value.items():
            ench = _resolve_enchantment(name)
            self.raw.addUnsafeEnchantment(ench, level)

    def add_enchantment(self, name: str, level: int):
        ench = _resolve_enchantment(name)
        self.raw.addUnsafeEnchantment(ench, level)

    def remove_enchantment(self, name: str):
        ench = _resolve_enchantment(name)
        self.raw.removeEnchantment(ench)

    @property
    def unbreakable(self) -> bool:
        meta = self.raw.getItemMeta()
        return meta.isUnbreakable() if meta is not None else False

    @unbreakable.setter
    def unbreakable(self, value: bool):
        meta = self.raw.getItemMeta()
        meta.setUnbreakable(value)
        self.raw.setItemMeta(meta)

    @property
    def custom_model_data(self) -> int:
        meta = self.raw.getItemMeta()
        if meta is not None and meta.hasCustomModelData():
            return meta.getCustomModelData()
        return None

    @custom_model_data.setter
    def custom_model_data(self, value: int):
        meta = self.raw.getItemMeta()
        meta.setCustomModelData(value)
        self.raw.setItemMeta(meta)

    @property
    def durability(self) -> int:
        meta = self.raw.getItemMeta()
        if meta is not None and hasattr(meta, "getDamage"):
            return meta.getDamage()
        return None

    @durability.setter
    def durability(self, value: int):
        meta = self.raw.getItemMeta()
        meta.setDamage(value)
        self.raw.setItemMeta(meta)

    @property
    def max_durability(self) -> int:
        if self.raw.hasData(_DataComponentTypes.MAX_DAMAGE):
            return self.raw.getData(_DataComponentTypes.MAX_DAMAGE).maxDamage()
        return self.raw.getType().getMaxDurability()

    @max_durability.setter
    def max_durability(self, value: int):
        self.raw.setData(_DataComponentTypes.MAX_DAMAGE, value)

    @property
    def custom_data(self) -> ItemCustomData:
        return ItemCustomData(self)

    @property
    def components(self) -> ComponentMap:
        return ComponentMap(self)

    def __repr__(self):
        return f"ItemStack({self.material}, x{self.amount})"


def itemstack_from(raw) -> ItemStack:
    if raw is None:
        return None
    meta = raw.getItemMeta() if raw.hasItemMeta() else None
    display_name = None
    lore = []
    if meta is not None:
        if meta.hasDisplayName():
            display_name = serialize_mini_message(meta.displayName())
        if meta.hasLore():
            lore = [serialize_mini_message(line) for line in meta.lore()]
    return ItemStack(
        material=raw.getType(),
        amount=raw.getAmount(),
        display_name=display_name,
        lore=lore,
        _raw=raw,
    )


@dataclass
class Inventory:
    raw: object

    @property
    def size(self) -> int:
        return self.raw.getSize()

    def get_item(self, slot: int) -> ItemStack:
        return itemstack_from(self.raw.getItem(slot))

    def set_item(self, slot: int, item: ItemStack):
        self.raw.setItem(slot, item.raw)

    def add_item(self, item: ItemStack):
        self.raw.addItem(item.raw)

    def remove_item(self, item: ItemStack):
        self.raw.removeItem(item.raw)

    def clear(self, slot: int = None):
        if slot is None:
            self.raw.clear()
        else:
            self.raw.clear(slot)

    @property
    def items(self) -> list[ItemStack]:
        return [itemstack_from(i) for i in self.raw.getContents() if i is not None]

    def __repr__(self):
        return f"Inventory(size={self.size})"