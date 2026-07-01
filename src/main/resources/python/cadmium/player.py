from dataclasses import dataclass
from cadmium.utils import mm, to_java_date
from cadmium.location import Location, location_from
from datetime import datetime
import java
from enum import Enum

GameMode = java.type("org.bukkit.GameMode")

@dataclass
class Player:
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
        ctx.sender.raw.kill()

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
