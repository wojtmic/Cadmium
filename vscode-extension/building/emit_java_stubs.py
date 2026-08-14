#!/usr/bin/env python3
"""Generate java_types.pyi from stub-dump.json (produced by /cadmium dumpstubs)."""
import json
import keyword
import re
import sys
from pathlib import Path

PRIMITIVES = {
    "int": "int", "long": "int", "short": "int", "byte": "int", "char": "str",
    "double": "float", "float": "float",
    "boolean": "bool",
    "void": "None",
}

LANG_MAP = {
    "java.lang.String": "str",
    "java.lang.Object": "object",
    "java.lang.Integer": "int",
    "java.lang.Long": "int",
    "java.lang.Short": "int",
    "java.lang.Byte": "int",
    "java.lang.Double": "float",
    "java.lang.Float": "float",
    "java.lang.Boolean": "bool",
    "java.lang.Character": "str",
    "java.lang.CharSequence": "str",
    "java.lang.Number": "float",
    "java.lang.Void": "None",
}

CONTAINER_MAP = {
    "java.util.List": "list",
    "java.util.Collection": "list",
    "java.util.Set": "set",
    "java.util.Map": "dict",
    "java.util.Optional": "Any",
    "com.google.common.collect.Multimap": "dict",
}

GENERIC_VAR_RE = re.compile(r"^[A-Z][0-9]?$")


def stub_name(java_name: str) -> str:
    return "J" + java_name.rsplit(".", 1)[-1].replace("$", "_")


def resolve_type(java_type: str, known: dict) -> str:
    if java_type.endswith("[]"):
        return f"list[{resolve_type(java_type[:-2], known)}]"
    if java_type in PRIMITIVES:
        return PRIMITIVES[java_type]
    if java_type in LANG_MAP:
        return LANG_MAP[java_type]
    if GENERIC_VAR_RE.match(java_type):
        return "Any"
    if java_type in known:
        return known[java_type]
    return CONTAINER_MAP.get(java_type, "Any")


def emit_class(cls: dict, known: dict) -> str:
    name = stub_name(cls["name"])
    lines = []

    if cls["is_enum"]:
        lines.append(f"class {name}:")
        for const in cls["enum_constants"]:
            lines.append(f"    {const}: {name}")
        if not cls["enum_constants"]:
            lines.append("    pass")
    else:
        bases = [known[b] for b in [cls.get("superclass"), *cls.get("interfaces", [])] if b in known]
        base_str = f"({', '.join(bases)})" if bases else ""
        lines.append(f"class {name}{base_str}:")
        if not cls["fields"] and not cls["methods"]:
            lines.append("    pass")

    if not cls["is_enum"]:
        for f in cls["fields"]:
            if not f["static"] or keyword.iskeyword(f["name"]):
                continue
            lines.append(f"    {f['name']}: {resolve_type(f['type'], known)}")

    # dedupe overloads by name - one permissive signature per method name
    by_name = {}
    for m in cls["methods"]:
        by_name.setdefault(m["name"], m)

    for mname, m in by_name.items():
        # `or`/`and`/`from` etc. exist on the real Java object but aren't
        # reachable via dot syntax in Python (keyword after a dot is a
        # SyntaxError) - only getattr(obj, "or")(...) would work, so
        # there's no honest `def` to emit. Skip rather than mis-stub.
        if keyword.iskeyword(mname):
            continue

        ret = resolve_type(m["return_type"], known)
        params = [] if m["static"] else ["self"]
        params += [f"arg{i}: {resolve_type(p, known)}" for i, p in enumerate(m["params"])]

        prefix = "    @staticmethod\n" if m["static"] else ""
        lines.append(f"{prefix}    def {mname}({', '.join(params)}) -> {ret}: ...")

    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: emit_java_stubs.py <stub-dump.json> <output-dir>")

    dump = json.loads(Path(sys.argv[1]).read_text())
    classes = dump["classes"]
    known = {c["name"]: stub_name(c["name"]) for c in classes}

    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "java_types.pyi"

    header = (
        '"""AUTO-GENERATED from stub-dump.json - regenerate, don\'t hand-edit."""\n'
        "from typing import Any\n\n"
    )
    body = "\n\n".join(emit_class(c, known) for c in classes)
    out_file.write_text(header + body + "\n")

    print(f"wrote {out_file} ({len(classes)} classes)")


if __name__ == "__main__":
    main()