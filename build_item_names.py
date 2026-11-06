"""build_item_names.py - official English item names for item_ids.json.

item_ids.json was made from the game's Japanese item ids, and its English
names were translated from those ("Augus' teff"), not taken from the game's
own English text ("Orgus Coffee").  The game's message files hold both
languages under the same label (MIID_AugusTeff), so the Japanese text there
matches an item's Japanese name exactly and the English text next to it is the
official name.  This rewrites the "en" field of every item it can match; items
it can't match keep their current name.

    python build_item_names.py <path to your dumped romfs folder>

(or set FEFW_ROM).  Forged copies (＋1 … ＋5) take the base item's name.
"""
import glob
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import msbt                                   # noqa: E402

ROM = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FEFW_ROM", "")


def jp_to_en_all(rom: str) -> dict[str, str]:
    """Japanese -> English from every message file; Item* files win on clashes."""
    jp_dir, en_dir = os.path.join(rom, "Msg", "JPja"), os.path.join(rom, "Msg", "EUen")
    out: dict[str, str] = {}
    files = sorted(glob.glob(os.path.join(jp_dir, "*.msbt*")),
                   key=lambda p: not os.path.basename(p).lower().startswith("item"))
    for jp_path in files:
        en_path = os.path.join(en_dir, os.path.basename(jp_path))
        if not os.path.isfile(en_path):
            continue
        try:
            pairs = msbt.jp_to_en(jp_path, en_path)
        except Exception as exc:              # noqa: BLE001 - skip a file we can't read
            print("  skipped %s: %s" % (os.path.basename(jp_path), exc))
            continue
        for jp, en in pairs.items():
            out.setdefault(jp, en)
    return out


def main() -> int:
    if not os.path.isdir(os.path.join(ROM, "Msg")):
        print("usage: python build_item_names.py <path to your dumped romfs folder>\n"
              "       (or set FEFW_ROM to it)")
        return 2
    names = jp_to_en_all(ROM)
    path = os.path.join(HERE, "item_ids.json")
    items = json.load(open(path, encoding="utf8"))
    changed = matched = 0
    for meta in items.values():
        jp = unicodedata.normalize("NFKC", meta.get("jp") or "").strip()
        m = re.search(r"\+(\d+)$", jp)
        base = jp[:m.start()] if m else jp
        en = names.get(jp) or names.get(base)
        if not en:
            continue
        matched += 1
        if m and not re.search(r"\+\s*\d+$", en):
            en = "%s +%s" % (en, m.group(1))
        if meta.get("en") != en:
            meta["en"] = en
            changed += 1
    with open(path, "w", encoding="utf8") as fh:
        json.dump(items, fh, ensure_ascii=False, separators=(",", ":"))
    print("%d items: %d matched the game's English text, %d names updated -> %s"
          % (len(items), matched, changed, path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
