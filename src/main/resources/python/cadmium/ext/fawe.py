from __future__ import annotations
from typing import TYPE_CHECKING
import java

from cadmium.ext.base import require_plugin_type
from cadmium.location import Location

if TYPE_CHECKING:
    from cadmium.player import Player

_BukkitAdapter = java.type("com.sk89q.worldedit.bukkit.BukkitAdapter")
_WorldEdit = java.type("com.sk89q.worldedit.WorldEdit")
_BlockVector3 = java.type("com.sk89q.worldedit.math.BlockVector3")
_CuboidRegion = java.type("com.sk89q.worldedit.regions.CuboidRegion")
_ParserContext = java.type("com.sk89q.worldedit.extension.factory.parser.ParserContext")
_ClipboardFormats = java.type("com.sk89q.worldedit.extent.clipboard.io.ClipboardFormats")
_BuiltInClipboardFormat = java.type("com.sk89q.worldedit.extent.clipboard.io.BuiltInClipboardFormat")
_BlockArrayClipboard = java.type("com.sk89q.worldedit.extent.clipboard.BlockArrayClipboard")
_ClipboardHolder = java.type("com.sk89q.worldedit.session.ClipboardHolder")
_ForwardExtentCopy = java.type("com.sk89q.worldedit.function.operation.ForwardExtentCopy")
_Operations = java.type("com.sk89q.worldedit.function.operation.Operations")
_File = java.type("java.io.File")
_FileInputStream = java.type("java.io.FileInputStream")
_FileOutputStream = java.type("java.io.FileOutputStream")


def _require_fawe():
    require_plugin_type("FastAsyncWorldEdit", "com.sk89q.worldedit.WorldEdit")
    return _WorldEdit.getInstance()

def _to_block_vector3(loc: Location):
    return _BlockVector3.at(int(loc.x), int(loc.y), int(loc.z))

def _parse_pattern(pattern: str, actor=None):
    we = _require_fawe()
    context = _ParserContext()
    if actor is not None:
        context.setActor(actor)
    return we.getPatternFactory().parseFromInput(pattern, context)

def _actor_from(p: "Player | None"):
    if p is None:
        return None
    return _BukkitAdapter.adapt(p.raw)

def fill(corner1: Location, corner2: Location, block: str, actor: "Player | None" = None) -> int:
    if corner1.world != corner2.world:
        raise ValueError("corner1 and corner2 must be in the same world")

    we = _require_fawe()
    we_world = _BukkitAdapter.adapt(corner1.world.raw)
    region = _CuboidRegion(_to_block_vector3(corner1), _to_block_vector3(corner2))
    pattern = _parse_pattern(block, _actor_from(actor))

    changed = 0
    with we.newEditSessionBuilder().world(we_world).build() as edit_session:
        changed = edit_session.setBlocks(region, pattern)
    return changed

def walls(corner1: Location, corner2: Location, block: str, actor: "Player | None" = None) -> int:
    if corner1.world != corner2.world:
        raise ValueError("corner1 and corner2 must be in the same world")

    we = _require_fawe()
    we_world = _BukkitAdapter.adapt(corner1.world.raw)
    region = _CuboidRegion(_to_block_vector3(corner1), _to_block_vector3(corner2))
    pattern = _parse_pattern(block, _actor_from(actor))

    changed = 0
    with we.newEditSessionBuilder().world(we_world).build() as edit_session:
        changed = edit_session.makeCuboidWalls(region, pattern)
    return changed

def sphere(center: Location, block: str, radius: float, filled: bool = True, actor: "Player | None" = None) -> int:
    we = _require_fawe()
    we_world = _BukkitAdapter.adapt(center.world.raw)
    pattern = _parse_pattern(block, _actor_from(actor))

    changed = 0
    with we.newEditSessionBuilder().world(we_world).build() as edit_session:
        changed = edit_session.makeSphere(_to_block_vector3(center), pattern, radius, filled)
    return changed

def cylinder(center: Location, block: str, radius: float, height: float, filled: bool = True, actor: "Player | None" = None) -> int:
    we = _require_fawe()
    we_world = _BukkitAdapter.adapt(center.world.raw)
    pattern = _parse_pattern(block, _actor_from(actor))

    changed = 0
    with we.newEditSessionBuilder().world(we_world).build() as edit_session:
        changed = edit_session.makeCylinder(_to_block_vector3(center), pattern, radius, height, filled)
    return changed

def replace(corner1: Location, corner2: Location, from_block: str, to_block: str, actor: "Player | None" = None) -> int:
    if corner1.world != corner2.world:
        raise ValueError("corner1 and corner2 must be in the same world")

    we = _require_fawe()
    we_world = _BukkitAdapter.adapt(corner1.world.raw)
    region = _CuboidRegion(_to_block_vector3(corner1), _to_block_vector3(corner2))
    actor_raw = _actor_from(actor)
    mask = we.getMaskFactory().parseFromInput(from_block, _ParserContext())
    pattern = _parse_pattern(to_block, actor_raw)

    changed = 0
    with we.newEditSessionBuilder().world(we_world).build() as edit_session:
        changed = edit_session.replaceBlocks(region, mask, pattern)
    return changed

def save_schematic(corner1: Location, corner2: Location, origin: Location, name: str):
    if corner1.world != corner2.world:
        raise ValueError("corner1 and corner2 must be in the same world")

    we = _require_fawe()
    we_world = _BukkitAdapter.adapt(corner1.world.raw)
    region = _CuboidRegion(we_world, _to_block_vector3(corner1), _to_block_vector3(corner2))

    clipboard = _BlockArrayClipboard(region)
    clipboard.setOrigin(_to_block_vector3(origin))

    with we.newEditSessionBuilder().world(we_world).build() as edit_session:
        copy = _ForwardExtentCopy(edit_session, region, clipboard, region.getMinimumPoint())
        _Operations.complete(copy)

    file = _File(name if name.endswith(".schem") else f"{name}.schem")
    with _BuiltInClipboardFormat.SPONGE_V3_SCHEMATIC.getWriter(_FileOutputStream(file)) as writer:
        writer.write(clipboard)

def load_schematic(name: str):
    _require_fawe()
    file = _File(name if name.endswith(".schem") else f"{name}.schem")
    fmt = _ClipboardFormats.findByFile(file)
    if fmt is None:
        raise ValueError(f"Could not detect schematic format for: {name}")

    with fmt.getReader(_FileInputStream(file)) as reader:
        return reader.read()

def paste_schematic(clipboard, at: Location, ignore_air: bool = True, actor: "Player | None" = None) -> int:
    we = _require_fawe()
    we_world = _BukkitAdapter.adapt(at.world.raw)

    changed = 0
    with we.newEditSessionBuilder().world(we_world).build() as edit_session:
        holder = _ClipboardHolder(clipboard)
        operation = (
            holder.createPaste(edit_session)
            .to(_to_block_vector3(at))
            .ignoreAirBlocks(ignore_air)
            .build()
        )
        _Operations.complete(operation)
        changed = edit_session.getBlockChangeCount()
    return changed