"""build_flag_names.py - flag id -> readable label for the Flags page.

The save's flag store (GameUserData) is [u8 kind][u32 fnv1_32(name)][value]:
the game writes the *name* of a variable, not an index.  So a flag can be
named by collecting every identifier the game stores in its data files and
hashing it the same way.

Sources
  GameData/*.bin        ASCII identifiers (null-terminated runs)
  supports.json         支援会話_<A>_<B>_<rank> -> "Support A - B (C)"
  unit_ids.json         PID_<x> -> 加入_<x> (recruited), 面識_<x> (met)

Writes flag_names.json: {"<hash8hex>": {"name": "<game name>", "label": "<EN>"}}
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fefw_core as core                      # noqa: E402

GAMEDATA = ("C:/Users/unbro/Downloads/Fire-Emblem-Fortunes-Weave-NS2/"
            "Fire-Emblem-Fortunes-Weave-NS2/FEFW ROM/131072/romfs/GameData")

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{2,63}$")
NAMEY = re.compile(r"^[^\s\d][^\s]{2,79}$")


def game_strings():
    """Null-terminated names from the game's data files, ASCII or Japanese."""
    out = set()
    for path in glob.glob(os.path.join(GAMEDATA, "*.bin")):
        data = open(path, "rb").read()
        start = 0
        for m in re.finditer(rb"\x00", data):
            run = data[start:m.start()]
            start = m.start() + 1
            if not 3 <= len(run) <= 80:
                continue
            try:
                s = run.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if not s.isprintable() or (" " in s) or ("\t" in s):
                continue
            if IDENT.match(s) or ("_" in s and NAMEY.match(s)):
                out.add(s)
    return out


def main() -> int:
    names: dict[int, dict] = {}

    def add(name: str, label: str | None = None):
        h = core.id_hash(name)
        if h not in names:
            names[h] = {"name": name, "label": label or name}

    for s in sorted(game_strings()):
        add(s)

    sup = json.load(open(os.path.join(HERE, "supports.json"), encoding="utf8"))
    for pair in sup.get("pairs", []):
        a, b = pair.get("a_en") or pair["a"], pair.get("b_en") or pair["b"]
        for rank, h in (pair.get("flags") or {}).items():
            n = "支援会話_%s_%s_%s" % (pair["a"], pair["b"], rank)
            names[h & 0xFFFFFFFF] = {"name": n,
                                     "label": "Support %s - %s (%s)" % (a, b, rank),
                                     "kind": "support"}

    units = json.load(open(os.path.join(HERE, "unit_ids.json"), encoding="utf8"))
    seen = set()
    for meta in units.values():
        pid = (meta or {}).get("pid") or ""
        if not pid.startswith("PID_"):
            continue
        key = pid[4:]
        if key in seen:
            continue
        seen.add(key)
        label = meta.get("name") or key
        add("加入_" + key, "Recruited: %s" % label)
        add("面識_" + key, "Met: %s" % label)

    path = os.path.join(HERE, "flag_names.json")
    out = {"%08x" % h: v for h, v in names.items()}
    with open(path, "w", encoding="utf8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print("%d flag names -> %s (%.0f KB)" % (len(out), path, os.path.getsize(path) / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
