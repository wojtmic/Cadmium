from dataclasses import dataclass, field
from cadmium.player import Player

@dataclass
class CommandContext:
    sender: object
    label: str
    argv: list = field(default_factory=list)

    @property
    def args(self):
        return self.argv


def _wrap_sender(raw_sender):
    return Player(raw=raw_sender)


def command(name: str, permission: str = None, completer=None):
    def decorator(func):
        def executor(sender, label, args):
            py_sender = _wrap_sender(sender)
            if permission and not sender.hasPermission(permission):
                py_sender.send("<red>You don't have permission.")
                return
            ctx = CommandContext(sender=py_sender, label=label, argv=list(args))
            func(ctx)

        def java_completer(sender, label, args):
            if completer is None:
                return []
            arg_id = len(args) - 1
            return completer(arg_id) or []

        _command_manager.register(name, executor, java_completer)
        return func
    return decorator