from dataclasses import dataclass, field
import java
from cadmium.utils import mm, serialize_mini_message

Material = java.type("org.bukkit.Material")
_ItemStack = java.type("org.bukkit.inventory.ItemStack")
_Bukkit = java.type("org.bukkit.Bukkit")
_Enchantment = java.type("org.bukkit.enchantments.Enchantment")
_NamespacedKey = java.type("org.bukkit.NamespacedKey")


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