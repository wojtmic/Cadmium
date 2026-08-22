import java
from dataclasses import dataclass
from cadmium.utils import mm, serialize_mini_message

_Bukkit = java.type("org.bukkit.Bukkit")

NameTagVisibility = java.type("org.bukkit.scoreboard.NameTagVisibility")
TeamOption = java.type("org.bukkit.scoreboard.Team$Option")
TeamOptionStatus = java.type("org.bukkit.scoreboard.Team$OptionStatus")


def _scoreboard():
    return _Bukkit.getScoreboardManager().getMainScoreboard()


@dataclass
class Team:
    raw: object

    @property
    def name(self) -> str:
        return self.raw.getName()

    @property
    def display_name(self) -> str:
        return serialize_mini_message(self.raw.displayName())

    @display_name.setter
    def display_name(self, value: str):
        self.raw.displayName(mm(value))

    @property
    def prefix(self) -> str:
        return serialize_mini_message(self.raw.prefix())

    @prefix.setter
    def prefix(self, value: str):
        self.raw.prefix(mm(value or ""))

    @property
    def suffix(self) -> str:
        return serialize_mini_message(self.raw.suffix())

    @suffix.setter
    def suffix(self, value: str):
        self.raw.suffix(mm(value or ""))

    @property
    def color(self):
        return self.raw.getColor()

    @color.setter
    def color(self, value):
        self.raw.setColor(value)

    @property
    def allow_friendly_fire(self) -> bool:
        return self.raw.allowFriendlyFire()

    @allow_friendly_fire.setter
    def allow_friendly_fire(self, value: bool):
        self.raw.setAllowFriendlyFire(value)

    @property
    def can_see_friendly_invisibles(self) -> bool:
        return self.raw.canSeeFriendlyInvisibles()

    @can_see_friendly_invisibles.setter
    def can_see_friendly_invisibles(self, value: bool):
        self.raw.setCanSeeFriendlyInvisibles(value)

    @property
    def name_tag_visibility(self):
        return self.raw.getNameTagVisibility()

    @name_tag_visibility.setter
    def name_tag_visibility(self, value):
        self.raw.setNameTagVisibility(value)

    @property
    def size(self) -> int:
        return self.raw.getSize()

    @property
    def entries(self) -> list[str]:
        return list(self.raw.getEntries())

    @property
    def players(self) -> list:
        from cadmium.player import Player
        return [Player(raw=p) for p in self.raw.getPlayers() if p.isOnline()]

    def add_player(self, player):
        self.raw.addPlayer(player.raw)

    def remove_player(self, player) -> bool:
        return self.raw.removePlayer(player.raw)

    def has_player(self, player) -> bool:
        return self.raw.hasPlayer(player.raw)

    def add_entry(self, entry: str):
        self.raw.addEntry(entry)

    def remove_entry(self, entry: str) -> bool:
        return self.raw.removeEntry(entry)

    def has_entry(self, entry: str) -> bool:
        return self.raw.hasEntry(entry)

    def get_option(self, option):
        return self.raw.getOption(option)

    def set_option(self, option, status):
        self.raw.setOption(option, status)

    def unregister(self):
        self.raw.unregister()

    def __eq__(self, other):
        if not isinstance(other, Team):
            return NotImplemented
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"Team({self.name!r}, size={self.size})"


def team_from(raw) -> Team | None:
    if raw is None:
        return None
    return Team(raw=raw)


def create_team(name: str) -> Team:
    return Team(raw=_scoreboard().registerNewTeam(name))


def get_team(name: str) -> Team | None:
    return team_from(_scoreboard().getTeam(name))


def get_all_teams() -> list[Team]:
    return [Team(raw=t) for t in _scoreboard().getTeams()]


def get_player_team(player) -> Team | None:
    return team_from(_scoreboard().getPlayerTeam(player.raw))
