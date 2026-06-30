import java

_MiniMessage = java.type("net.kyori.adventure.text.minimessage.MiniMessage")

def mm(text: str):
    return _MiniMessage.miniMessage().deserialize(text)
