from dataclasses import dataclass
from cadmium.utils import mm, to_java_date
from cadmium.location import Location, location_from
from cadmium.inventory import Inventory, ItemStack, itemstack_from
from cadmium.living_entity import LivingEntity
from datetime import datetime
import java
from enum import Enum

_Bukkit = java.type("org.bukkit.Bukkit")

GameMode = java.type("org.bukkit.GameMode")

@dataclass
class Player(LivingEntity):
    raw: object

    @property
    def name(self) -> str:
        return self.raw.getName()

    @property
    def display_name(self):
        return self.raw.displayName()

    @display_name.setter
    def display_name(self, value: str):
        self.raw.displayName(mm(value))

    def kick(self, msg: str = 'Kicked by an operator.'):
        self.raw.kick(mm(msg))

    def ban(self, msg: str = 'Banned by an operator.'):
        self.raw.ban(mm(msg), None, None, True)

    def tempban(self, expires: datetime | int, msg: str = 'Banned by an operator.'):
        self.raw.ban(mm(msg), to_java_date(expires), None, True)

    def send(self, msg: str):
        self.raw.sendMessage(mm(msg))

    @property
    def sneaking(self) -> bool:
        return self.raw.isSneaking()

    @sneaking.setter
    def sneaking(self, state: bool):
        return self.raw.setSneaking(state)

    @property
    def sprinting(self) -> bool:
        return self.raw.isSprinting()

    @sprinting.setter
    def sprinting(self, state: bool):
        return self.raw.setSprinting(state)

    def send_actionbar(self, text: str):
        self.raw.sendActionBar(mm(text))

    def send_title(self, title: str, subtitle: str = '', fade_in: int = 10, stay: int = 70, fade_out: int = 20):
        Title = java.type("net.kyori.adventure.title.Title")
        Times = java.type("net.kyori.adventure.title.Title$Times")
        Duration = java.type("java.time.Duration")
        times = Times.times(
            Duration.ofMillis(fade_in * 50),
            Duration.ofMillis(stay * 50),
            Duration.ofMillis(fade_out * 50)
        )
        self.raw.showTitle(Title.title(mm(title), mm(subtitle), times))

    @property
    def health(self) -> float:
        return self.raw.getHealth()

    @health.setter
    def health(self, val: float):
        self.raw.setHealth(val)

    def kill(self):
        self.raw.kill()

    @property
    def food_level(self) -> int:
        return self.raw.getFoodLevel()

    @food_level.setter
    def food_level(self, val: int):
        self.raw.setFoodLevel(val)

    @property
    def gamemode(self) -> GameMode:
        return self.raw.getGameMode()

    @gamemode.setter
    def gamemode(self, val: GameMode):
        self.raw.setGameMode(val)

    @property
    def location(self) -> Location:
        return location_from(self.raw.getLocation())

    @location.setter
    def location(self, loc: Location):
        self.raw.teleport(loc.raw)

    @property
    def x(self) -> float:
        return self.location.x

    @property
    def y(self) -> float:
        return self.location.y

    @property
    def z(self) -> float:
        return self.location.z

    @property
    def yaw(self) -> float:
        return self.location.yaw

    @property
    def pitch(self) -> float:
        return self.location.pitch

    @property
    def world(self):
        return self.location.world

    @property
    def inventory(self) -> Inventory:
        return Inventory(raw=self.raw.getInventory())

    def give(self, item: ItemStack):
        self.inventory.add_item(item)

    @property
    def tool(self) -> ItemStack:
        return itemstack_from(self.raw.getInventory().getItemInMainHand())

    @tool.setter
    def tool(self, item: ItemStack):
        self.raw.getInventory().setItemInMainHand(item.raw)

    @property
    def off_hand(self) -> ItemStack:
        return itemstack_from(self.raw.getInventory().getItemInOffHand())

    @off_hand.setter
    def off_hand(self, item: ItemStack):
        self.raw.getInventory().setItemInOffHand(item.raw)

    @property
    def helmet(self) -> ItemStack:
        return itemstack_from(self.raw.getInventory().getHelmet())

    @helmet.setter
    def helmet(self, item: ItemStack):
        self.raw.getInventory().setHelmet(item.raw)

    @property
    def chestplate(self) -> ItemStack:
        return itemstack_from(self.raw.getInventory().getChestplate())

    @chestplate.setter
    def chestplate(self, item: ItemStack):
        self.raw.getInventory().setChestplate(item.raw)

    @property
    def leggings(self) -> ItemStack:
        return itemstack_from(self.raw.getInventory().getLeggings())

    @leggings.setter
    def leggings(self, item: ItemStack):
        self.raw.getInventory().setLeggings(item.raw)

    @property
    def boots(self) -> ItemStack:
        return itemstack_from(self.raw.getInventory().getBoots())

    @boots.setter
    def boots(self, item: ItemStack):
        self.raw.getInventory().setBoots(item.raw)

    def chat_as(self, message: str):
        self.raw.chat(message)

    def run_command_as(self, command: str, override_perms: bool = False):
        if not override_perms:
            self.raw.performCommand(command)
            return

        attachment = self.raw.addAttachment(_plugin)
        attachment.setPermission("*", True)
        try:
            self.raw.performCommand(command)
        finally:
            self.raw.removeAttachment(attachment)

    def send_resource_pack(self, uri: str, hash: str = None, required: bool = False, prompt: str = None):
        ResourcePackRequest = java.type("net.kyori.adventure.resource.ResourcePackRequest")
        ResourcePackInfo = java.type("net.kyori.adventure.resource.ResourcePackInfo")
        UUID = java.type("java.util.UUID")

        info = ResourcePackInfo.resourcePackInfo(UUID.randomUUID(), java.type("java.net.URI").create(uri), "" if hash is None else hash)

        builder = ResourcePackRequest.resourcePackRequest().packs(info).required(required)
        if prompt is not None:
            builder = builder.prompt(mm(prompt))

        self.raw.sendResourcePacks(builder.build())

    def remove_resource_packs(self, *uuids):
        self.raw.removeResourcePacks(*uuids) if uuids else self.raw.removeResourcePacks()

    @property
    def blocking(self) -> bool:
        return self.raw.isBlocking()

    def play_sound(self, sound: str, volume: float = 1, pitch: float = 1):
        self.raw.playSound(self.raw.getLocation(), sound, volume, pitch)

    def display_particle(self, particle: str, count: int = 1, offset_x: float = 0, offset_y: float = 0, offset_z: float = 0, extra: float = 0, data=None):
        Registry = java.type("org.bukkit.Registry")
        NamespacedKey = java.type("org.bukkit.NamespacedKey")
        p = Registry.PARTICLE_TYPE.get(NamespacedKey.minecraft(particle))
        if data is not None:
            self.raw.spawnParticle(p, self.raw.getLocation(), count, offset_x, offset_y, offset_z, extra, data)
        else:
            self.raw.spawnParticle(p, self.raw.getLocation(), count, offset_x, offset_y, offset_z, extra)

    @property
    def fastboard_title(self) -> str:
        from cadmium.fastboard import _entry
        entry = _entry(self)
        return entry[1] if entry else ""

    @fastboard_title.setter
    def fastboard_title(self, title: str):
        from cadmium.fastboard import _get_or_create
        entry = _get_or_create(self)
        entry[0].updateTitle(mm(title))
        entry[1] = title

    @property
    def fastboard(self) -> list:
        from cadmium.fastboard import _get_or_create
        entry = _get_or_create(self)
        return entry[2]

    @fastboard.setter
    def fastboard(self, lines: list):
        if len(lines) > 15:
            raise ValueError(f"fastboard supports at most 15 lines, got {len(lines)}")
        from cadmium.fastboard import _get_or_create, _FastboardLines
        entry = _get_or_create(self)
        entry[0].updateLines([mm(line) for line in lines])
        entry[2] = _FastboardLines(entry[0], lines)

    def clear_fastboard(self):
        from cadmium.fastboard import _clear
        _clear(self)

def find_player(name: str):
    raw = _Bukkit.getPlayerExact(name)
    if raw is None:
        return None

    return Player(raw=raw)

def get_all_players() -> list:
    return [Player(raw=p) for p in _Bukkit.getOnlinePlayers()]

def play_sound_at_location(loc: Location, sound: str, volume: float = 1, pitch: float = 1):
    loc.world.raw.playSound(loc.raw, sound, volume, pitch)

def display_particle_at_location(loc: Location, particle: str, count: int = 1, offset_x: float = 0, offset_y: float = 0, offset_z: float = 0, extra: float = 0, data=None):
    Registry = java.type("org.bukkit.Registry")
    NamespacedKey = java.type("org.bukkit.NamespacedKey")
    p = Registry.PARTICLE_TYPE.get(NamespacedKey.minecraft(particle))
    if data is not None:
        loc.world.raw.spawnParticle(p, loc.raw, count, offset_x, offset_y, offset_z, extra, data)
    else:
        loc.world.raw.spawnParticle(p, loc.raw, count, offset_x, offset_y, offset_z, extra)

def dust_options(color: tuple[int, int, int], size: float = 1.0):
    DustOptions = java.type("org.bukkit.Particle$DustOptions")
    Color = java.type("org.bukkit.Color")
    r, g, b = color
    return DustOptions(Color.fromRGB(r, g, b), size)

Material = java.type('org.bukkit.Material')
def item_particle(mat: Material):
    ItemStack = java.type("org.bukkit.inventory.ItemStack")
    return ItemStack(mat)