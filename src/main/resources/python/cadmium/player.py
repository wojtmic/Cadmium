from dataclasses import dataclass
from cadmium.utils import mm


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

    def send(self, msg: str):
        self.raw.sendMessage(mm(msg))
