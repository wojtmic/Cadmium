from cadmium.ext.base import require_plugin_type

def resolve(p, val):
    papi = require_plugin_type("PlaceholderAPI", "me.clip.placeholderapi.PlaceholderAPI")
    return papi.setPlaceholders(p.raw, val)
