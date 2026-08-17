import java

class CadmiumMissingExtensionDependencyException(Exception):
    pass

_Bukkit = java.type('org.bukkit.Bukkit')
_type_cache = {}

def require_plugin_type(plugin_name: str, class_name: str):
    """
    Lazily resolves a Java class from another plugin, raising
    CadmiumMissingExtensionDependencyException if that plugin
    isn't installed/enabled.
    """
    cache_key = (plugin_name, class_name)
    if cache_key in _type_cache:
        return _type_cache[cache_key]

    plugin = _Bukkit.getPluginManager().getPlugin(plugin_name)
    if plugin is None or not plugin.isEnabled():
        raise CadmiumMissingExtensionDependencyException(
            f'You need to have {plugin_name} installed to use this feature!'
        )

    resolved = java.type(class_name)
    _type_cache[cache_key] = resolved
    return resolved
