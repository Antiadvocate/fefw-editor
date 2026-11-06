"""build_skill_ids.py - SID hash -> name for the Arts & skills tab.

The skill lists inside a unit record hold `low32(fnv1_64("SID_…"))`.  Skill.bin
carries those keys (SID_旋風槍), and Msg/{JPja,EUen}/Skill.msbt.zst carries the
same entries in the same order, so a key's Japanese half matches its Japanese
text exactly and the English text of that label is the English name.

Writes skill_ids.json: {"<hash8hex>": {"sid": "SID_…", "jp": "…", "en": "…"}}
Rebuild it for a different game version:
    python build_skill_ids.py [romfs dir]
"""
import glob
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fefw_core as core                      # noqa: E402

ROM = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FEFW_ROM", "")


def sid_keys() -> list:
    out = set()
    for path in glob.glob(os.path.join(ROM, "GameData", "Skill*.bin")):
        data = open(path, "rb").read()
        start = 0
        for m in re.finditer(rb"\x00", data):
            run = data[start:m.start()]
            start = m.start() + 1
            if run.startswith(b"SID_") and 5 < len(run) <= 80:
                try:
                    out.add(run.decode("utf-8"))
                except UnicodeDecodeError:
                    pass
    return sorted(out)


def main() -> int:
    if not os.path.isdir(os.path.join(ROM, "GameData")):
        print("usage: python build_skill_ids.py <path to your dumped romfs folder>\n"
              "       (or set FEFW_ROM to it)")
        return 2
    # matched by label, not by position: labels aren't stored in text order
    import msbt
    jp_to_en = msbt.jp_to_en(os.path.join(ROM, "Msg", "JPja", "Skill.msbt.zst"),
                             os.path.join(ROM, "Msg", "EUen", "Skill.msbt.zst"))
    out = {}
    for sid in sid_keys():
        jp = sid[4:]
        out["%08x" % core.id_hash(sid)] = {"sid": sid, "jp": jp, "en": jp_to_en.get(jp, "")}
    path = os.path.join(HERE, "skill_ids.json")
    with open(path, "w", encoding="utf8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    named = sum(1 for v in out.values() if v["en"])
    print("%d skill ids (%d with an English name) -> %s" % (len(out), named, path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
