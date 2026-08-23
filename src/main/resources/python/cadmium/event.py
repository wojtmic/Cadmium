from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union
from cadmium.player import Player, GameMode
from cadmium.entity import Entity, entity_from_raw
from cadmium.inventory import itemstack_from, Inventory
from cadmium.vector import Vector, vector_from
from cadmium.location import Location, location_from
from cadmium.block import block_from
import java

FishState = java.type("org.bukkit.event.player.PlayerFishEvent$State")

if TYPE_CHECKING:
    from cadmium.living_entity import LivingEntity
    from java_types import (
        JEntityKnockbackEvent,
        JEntityPushedByEntityAttackEvent,
        JEntityDeathEvent,
        JPlayerDeathEvent,
        JPlayerJoinEvent,
        JPlayerQuitEvent,
        JPlayerCommandPreprocessEvent,
        JBlockBreakEvent,
        JBlockPlaceEvent,
        JEntitySpawnEvent,
        JPlayerFishEvent,
        JPlayerGameModeChangeEvent,
        JEntityDamageEvent,
        JPlayerInteractEntityEvent,
        JAsyncChatEvent,
        JPlayerMoveEvent,
        JInventoryClickEvent,
        JPlayerDropItemEvent,
        JPlayerSwapHandItemsEvent,
    )

def _wrap_player(raw):
    p = raw.getPlayer() if hasattr(raw, 'getPlayer') else None
    return Player(raw=p) if p is not None else None


class _CancellableMixin:
    _cancel_window_closed: bool = False

    def _close_cancel_window(self):
        self._cancel_window_closed = True

    def _guarded_cancel(self):
        if self._cancel_window_closed:
            raise RuntimeError(
                "event.cancel() called after the handler's first await - "
                "this is too late, the underlying event has already been "
                "processed by the server. Call event.cancel() before your "
                "first await, or restructure the handler so the decision "
                "to cancel happens synchronously."
            )
        self.raw.setCancelled(True)


@dataclass
class Event(_CancellableMixin):
    raw: object
    player: Player = field(default=None, init=False)

    def __post_init__(self):
        self.player = _wrap_player(self.raw)
        self._cancel_window_closed = False

    def cancel(self):
        self._guarded_cancel()

@dataclass
class PlayerJoinEvent:
    raw: "JPlayerJoinEvent"

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def join_message(self) -> Union[str, None]:
        from cadmium.utils import serialize_mini_message
        message = self.raw.joinMessage()
        return serialize_mini_message(message) if message is not None else None

    @join_message.setter
    def join_message(self, value: Union[str, None]):
        from cadmium.utils import mm
        self.raw.joinMessage(mm(value) if value is not None else None)

    def __repr__(self):
        return f"PlayerJoinEvent({self.player})"

@dataclass
class PlayerQuitEvent:
    raw: "JPlayerQuitEvent"

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def reason(self):
        return self.raw.getReason()

    @property
    def quit_message(self) -> Union[str, None]:
        from cadmium.utils import serialize_mini_message
        message = self.raw.quitMessage()
        return serialize_mini_message(message) if message is not None else None

    @quit_message.setter
    def quit_message(self, value: Union[str, None]):
        from cadmium.utils import mm
        self.raw.quitMessage(mm(value) if value is not None else None)

    def __repr__(self):
        return f"PlayerQuitEvent({self.player})"

@dataclass
class CommandEvent(_CancellableMixin):
    raw: "JPlayerCommandPreprocessEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def message(self) -> str:
        return self.raw.getMessage()

    @message.setter
    def message(self, value: str):
        self.raw.setMessage(value)

    @property
    def recipients(self) -> list:
        return [Player(raw=p) for p in self.raw.getRecipients()]

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"CommandEvent({self.player}, {self.message!r})"

@dataclass
class BlockBreakEvent(_CancellableMixin):
    raw: "JBlockBreakEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def block(self):
        return block_from(self.raw.getBlock())

    @property
    def drop_items(self) -> bool:
        return self.raw.isDropItems()

    @drop_items.setter
    def drop_items(self, value: bool):
        self.raw.setDropItems(value)

    @property
    def exp_to_drop(self) -> int:
        return self.raw.getExpToDrop()

    @exp_to_drop.setter
    def exp_to_drop(self, value: int):
        self.raw.setExpToDrop(value)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"BlockBreakEvent({self.player}, {self.block})"

@dataclass
class BlockPlaceEvent(_CancellableMixin):
    raw: "JBlockPlaceEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def block(self):
        return block_from(self.raw.getBlockPlaced())

    @property
    def block_against(self):
        return block_from(self.raw.getBlockAgainst())

    @property
    def item_in_hand(self):
        item = self.raw.getItemInHand()
        return itemstack_from(item) if item is not None else None

    @property
    def can_build(self) -> bool:
        return self.raw.canBuild()

    @can_build.setter
    def can_build(self, value: bool):
        self.raw.setBuild(value)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"BlockPlaceEvent({self.player}, {self.block})"

@dataclass
class EntitySpawnEvent(_CancellableMixin):
    raw: "JEntitySpawnEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def entity(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getEntity())

    @property
    def location(self) -> Location:
        return location_from(self.raw.getLocation())

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"EntitySpawnEvent({self.entity})"

@dataclass
class PlayerFishEvent(_CancellableMixin):
    raw: "JPlayerFishEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def caught(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getCaught())

    @property
    def hook(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getHook())

    @property
    def hand(self):
        return self.raw.getHand()

    @property
    def state(self) -> "FishState":
        return self.raw.getState()

    @property
    def exp_to_drop(self) -> int:
        return self.raw.getExpToDrop()

    @exp_to_drop.setter
    def exp_to_drop(self, value: int):
        self.raw.setExpToDrop(value)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerFishEvent({self.player}, {self.state})"

@dataclass
class PlayerGameModeChangeEvent(_CancellableMixin):
    raw: "JPlayerGameModeChangeEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def new_gamemode(self) -> GameMode:
        return self.raw.getNewGameMode()

    @new_gamemode.setter
    def new_gamemode(self, value: GameMode):
        self.raw.setNewGameMode(value)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerGameModeChangeEvent({self.player}, {self.new_gamemode})"

@dataclass
class EntityKnockbackEvent(_CancellableMixin):
    raw: "JEntityKnockbackEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def entity(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getEntity())

    @property
    def cause(self):
        return self.raw.getCause()

    @property
    def knockback(self) -> Vector:
        return vector_from(self.raw.getKnockback())

    @knockback.setter
    def knockback(self, vec: Vector):
        self.raw.setKnockback(vec.raw)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"EntityKnockbackEvent({self.entity}, {self.cause})"

@dataclass
class EntityPushedByEntityAttackEvent(_CancellableMixin):
    raw: "JEntityPushedByEntityAttackEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def entity(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getEntity())

    @property
    def attacker(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getPushedBy())

    @property
    def cause(self):
        return self.raw.getCause()

    @property
    def knockback(self) -> Vector:
        return vector_from(self.raw.getKnockback())

    @knockback.setter
    def knockback(self, vec: Vector):
        self.raw.setKnockback(vec.raw)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"EntityPushedByEntityAttackEvent({self.entity}, {self.attacker})"

@dataclass
class EntityDeathEvent:
    raw: "JEntityDeathEvent"

    @property
    def entity(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getEntity())

    @property
    def killer(self) -> Union[Player, "LivingEntity", Entity, None]:
        killer = self.raw.getEntity().getKiller()
        return entity_from_raw(killer) if killer is not None else None

    @property
    def drops(self) -> list:
        return [itemstack_from(i) for i in self.raw.getDrops()]

    def clear_drops(self):
        self.raw.getDrops().clear()

    def add_drop(self, item):
        self.raw.getDrops().add(item.raw)

    @property
    def dropped_exp(self) -> int:
        return self.raw.getDroppedExp()

    @dropped_exp.setter
    def dropped_exp(self, value: int):
        self.raw.setDroppedExp(value)

    def __repr__(self):
        return f"EntityDeathEvent({self.entity})"


@dataclass
class PlayerDeathEvent(_CancellableMixin):
    raw: "JPlayerDeathEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def killer(self) -> Union[Player, "LivingEntity", Entity, None]:
        killer = self.raw.getEntity().getKiller()
        return entity_from_raw(killer) if killer is not None else None

    @property
    def drops(self) -> list:
        return [itemstack_from(i) for i in self.raw.getDrops()]

    def clear_drops(self):
        self.raw.getDrops().clear()

    def add_drop(self, item):
        self.raw.getDrops().add(item.raw)

    @property
    def dropped_exp(self) -> int:
        return self.raw.getDroppedExp()

    @dropped_exp.setter
    def dropped_exp(self, value: int):
        self.raw.setDroppedExp(value)

    @property
    def death_message(self) -> str:
        from cadmium.utils import serialize_mini_message
        return serialize_mini_message(self.raw.deathMessage())

    @death_message.setter
    def death_message(self, value: str):
        from cadmium.utils import mm
        self.raw.deathMessage(mm(value))

    @property
    def keep_inventory(self) -> bool:
        return self.raw.getKeepInventory()

    @keep_inventory.setter
    def keep_inventory(self, value: bool):
        self.raw.setKeepInventory(value)

    @property
    def keep_level(self) -> bool:
        return self.raw.getKeepLevel()

    @keep_level.setter
    def keep_level(self, value: bool):
        self.raw.setKeepLevel(value)

    @property
    def new_exp(self) -> int:
        return self.raw.getNewExp()

    @new_exp.setter
    def new_exp(self, value: int):
        self.raw.setNewExp(value)

    @property
    def new_level(self) -> int:
        return self.raw.getNewLevel()

    @new_level.setter
    def new_level(self, value: int):
        self.raw.setNewLevel(value)

    @property
    def new_total_exp(self) -> int:
        return self.raw.getNewTotalExp()

    @new_total_exp.setter
    def new_total_exp(self, value: int):
        self.raw.setNewTotalExp(value)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerDeathEvent({self.player})"


@dataclass
class EntityDamageEvent(_CancellableMixin):
    raw: "JEntityDamageEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def entity(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getEntity())

    @property
    def player(self) -> Player:
        return self.entity

    @property
    def damage(self) -> float:
        return self.raw.getDamage()

    @damage.setter
    def damage(self, value: float):
        self.raw.setDamage(value)

    @property
    def final_damage(self) -> float:
        return self.raw.getFinalDamage()

    @property
    def cause(self):
        return self.raw.getCause()

    @property
    def attacker(self) -> Union[Player, "LivingEntity", Entity, None]:
        if hasattr(self.raw, "getDamager"):
            return entity_from_raw(self.raw.getDamager())
        return None

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"EntityDamageEvent({self.entity}, {self.damage})"


@dataclass
class PlayerInteractEntityEvent(_CancellableMixin):
    raw: "JPlayerInteractEntityEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def entity(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getRightClicked())

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerInteractEntityEvent({self.player}, {self.entity})"

@dataclass
class ChatEvent(_CancellableMixin):
    raw: "JAsyncChatEvent"
    player: Player = field(default=None, init=False)

    def __post_init__(self):
        self.player = _wrap_player(self.raw)
        self._cancel_window_closed = False

    @property
    def message(self) -> str:
        from cadmium.utils import serialize_mini_message
        return serialize_mini_message(self.raw.message())

    @message.setter
    def message(self, value: str):
        from cadmium.utils import mm
        self.raw.message(mm(value))

    @property
    def original_message(self) -> str:
        from cadmium.utils import serialize_mini_message
        return serialize_mini_message(self.raw.originalMessage())

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"ChatEvent({self.player}, {self.message!r})"

@dataclass
class PlayerMoveEvent(_CancellableMixin):
    raw: "JPlayerMoveEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def from_(self) -> Location:
        return location_from(self.raw.getFrom())

    @property
    def to(self) -> Location:
        return location_from(self.raw.getTo())

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerMoveEvent({self.player}, {self.from_} -> {self.to})"

@dataclass
class EntityDamageItemEvent(_CancellableMixin):
    raw: "JEntityDamageItemEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def entity(self) -> Union[Player, "LivingEntity", Entity, None]:
        return entity_from_raw(self.raw.getEntity())

    @property
    def item(self):
        return itemstack_from(self.raw.getItem())

    @property
    def damage(self) -> int:
        return self.raw.getDamage()

    @damage.setter
    def damage(self, value: int):
        self.raw.setDamage(value)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"EntityDamageItemEvent({self.entity}, {self.item}, {self.damage})"

@dataclass
class PlayerInteractEvent(_CancellableMixin):
    raw: "JPlayerInteractEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def action(self):
        return self.raw.getAction()

    @property
    def item(self):
        item = self.raw.getItem()
        return itemstack_from(item) if item is not None else None

    @property
    def block(self):
        return block_from(self.raw.getClickedBlock())

    @property
    def is_right_click(self) -> bool:
        return self.raw.getAction().name().startswith("RIGHT_CLICK")

    @property
    def is_left_click(self) -> bool:
        return self.raw.getAction().name().startswith("LEFT_CLICK")

    @property
    def is_block_click(self) -> bool:
        return self.raw.getAction().name().endswith("CLICK_BLOCK")

    @property
    def is_air_click(self) -> bool:
        return self.raw.getAction().name().endswith("CLICK_AIR")

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerInteractEvent({self.player}, {self.action})"

@dataclass
class InventoryClickEvent(_CancellableMixin):
    raw: "JInventoryClickEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getWhoClicked())

    @property
    def inventory(self) -> Inventory:
        return Inventory(raw=self.raw.getInventory())

    @property
    def clicked_inventory(self) -> Union[Inventory, None]:
        inv = self.raw.getClickedInventory()
        return Inventory(raw=inv) if inv is not None else None

    @property
    def slot(self) -> int:
        return self.raw.getSlot()

    @property
    def raw_slot(self) -> int:
        return self.raw.getRawSlot()

    @property
    def slot_type(self):
        return self.raw.getSlotType()

    @property
    def current_item(self):
        item = self.raw.getCurrentItem()
        return itemstack_from(item) if item is not None else None

    @current_item.setter
    def current_item(self, value):
        self.raw.setCurrentItem(value.raw if value is not None else None)

    @property
    def cursor(self):
        item = self.raw.getCursor()
        return itemstack_from(item) if item is not None else None

    @property
    def click_type(self):
        return self.raw.getClick()

    @property
    def action(self):
        return self.raw.getAction()

    @property
    def hotbar_button(self) -> int:
        return self.raw.getHotbarButton()

    @property
    def is_shift_click(self) -> bool:
        return self.raw.isShiftClick()

    @property
    def is_right_click(self) -> bool:
        return self.raw.isRightClick()

    @property
    def is_left_click(self) -> bool:
        return self.raw.isLeftClick()

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"InventoryClickEvent(slot={self.slot}, action={self.action})"

@dataclass
class PlayerDropItemEvent(_CancellableMixin):
    raw: "JPlayerDropItemEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def entity(self):
        from cadmium.entity import entity_from_raw
        return entity_from_raw(self.raw.getItemDrop())

    @property
    def item(self):
        item = self.raw.getItemDrop().getItemStack()
        return itemstack_from(item) if item is not None else None

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerDropItemEvent({self.player}, {self.item})"

@dataclass
class PlayerSwapHandItemsEvent(_CancellableMixin):
    raw: "JPlayerSwapHandItemsEvent"
    _cancel_window_closed: bool = field(default=False, init=False, repr=False)

    @property
    def player(self) -> Player:
        return Player(raw=self.raw.getPlayer())

    @property
    def main_hand_item(self):
        item = self.raw.getMainHandItem()
        return itemstack_from(item) if item is not None else None

    @main_hand_item.setter
    def main_hand_item(self, value):
        self.raw.setMainHandItem(value.raw if value is not None else None)

    @property
    def offhand_item(self):
        item = self.raw.getOffHandItem()
        return itemstack_from(item) if item is not None else None

    @offhand_item.setter
    def offhand_item(self, value):
        self.raw.setOffHandItem(value.raw if value is not None else None)

    def cancel(self):
        self._guarded_cancel()

    def __repr__(self):
        return f"PlayerSwapHandItemsEvent({self.player})"
