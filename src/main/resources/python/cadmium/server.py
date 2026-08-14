import java
from cadmium.utils import mm

_Bukkit = java.type("org.bukkit.Bukkit")


class _Server:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def raw(self):
        return _Bukkit.getServer()

    @property
    def online_players(self) -> int:
        return self.raw.getOnlinePlayers().size()

    @property
    def max_players(self) -> int:
        return self.raw.getMaxPlayers()

    @property
    def tps(self) -> list:
        return list(self.raw.getTPS())

    @property
    def version(self) -> str:
        return self.raw.getVersion()

    def console_command(self, command: str):
        _Bukkit.dispatchCommand(_Bukkit.getConsoleSender(), command)

    def shutdown(self):
        self.raw.shutdown()

    def __repr__(self):
        return f"Server(online={self.online_players}/{self.max_players})"


Server = _Server()