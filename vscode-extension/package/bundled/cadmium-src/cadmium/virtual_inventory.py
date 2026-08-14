import java
from cadmium.inventory import Inventory
from cadmium.utils import mm

_Bukkit = java.type("org.bukkit.Bukkit")
_InventoryType = java.type("org.bukkit.event.inventory.InventoryType")

InventoryType = _InventoryType


def create_inventory(size: int = 27, title: str = "Inventory") -> Inventory:
    raw = _Bukkit.createInventory(None, size, mm(title))
    return Inventory(raw=raw)


def create_typed_inventory(inv_type, title: str = None) -> Inventory:
    if title is not None:
        raw = _Bukkit.createInventory(None, inv_type, mm(title))
    else:
        raw = _Bukkit.createInventory(None, inv_type)
    return Inventory(raw=raw)


def open_inventory(player, inventory: Inventory):
    player.raw.openInventory(inventory.raw)


def close_inventory(player):
    player.raw.closeInventory()