from dataclasses import dataclass, field
import java
from cadmium.utils import mm

Material = java.type("org.bukkit.Material")
_ItemStack = java.type("org.bukkit.inventory.ItemStack")
_Bukkit = java.type("org.bukkit.Bukkit")


@dataclass
class ItemStack:
    material: object
    amount: int = 1
    display_name: str = None
    lore: list = field(default_factory=list)

    @property
    def raw(self):
        item = _ItemStack(self.material, self.amount)
        if self.display_name is not None or self.lore:
            meta = item.getItemMeta()
            if self.display_name is not None:
                meta.displayName(mm(self.display_name))
            if self.lore:
                meta.lore([mm(line) for line in self.lore])
            item.setItemMeta(meta)
        return item

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
            display_name = str(meta.displayName())
        if meta.hasLore():
            lore = [str(line) for line in meta.lore()]
    return ItemStack(
        material=raw.getType(),
        amount=raw.getAmount(),
        display_name=display_name,
        lore=lore,
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