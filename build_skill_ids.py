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


def msbt_pairs(path):
    """(labels, texts) from a decompressed .msbt.zst - texts by label index."""
    import zstandard
    raw = zstandard.ZstdDecompressor().decompressobj().decompress(open(path, "rb").read())
    utf16 = raw[0x0C:0x0E] == b"\xff\xfe"
    base = raw.find(b"LBL1") + 8
    n = struct.unpack_from("<I", raw, base + 8)[0]
    labels = []
    for k in range(n):
        cnt, off = struct.unpack_from("<II", raw, base + 12 + 8 * k)
        at = base + 8 + off
        for _ in range(cnt):
            ln = raw[at]
            at += 1
            labels.append(raw[at:at + ln].decode("ascii", "replace"))
            at += ln + 4
    t = raw.find(b"TXT2") + 8
    tn = struct.unpack_from("<I", raw, t + 8)[0]
    texts = []
    for k in range(tn):
        off = struct.unpack_from("<I", raw, t + 12 + 4 * k)[0]
        at = t + 8 + off
        if utf16:
            end = at
            while raw[end:end + 2] != b"\x00\x00":
                end += 2
            texts.append(raw[at:end].decode("utf-16-le", "replace"))
        else:
            end = raw.find(b"\x00", at)
            texts.append(raw[at:end].decode("utf-8", "replace"))
    return labels, texts


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
    jp_labels, jp_texts = msbt_pairs(os.path.join(ROM, "Msg", "JPja", "Skill.msbt.zst"))
    en_labels, en_texts = msbt_pairs(os.path.join(ROM, "Msg", "EUen", "Skill.msbt.zst"))
    en_by_index = {l: i for i, l in enumerate(en_labels)}
    jp_to_en = {}
    for lab, i in en_by_index.items():
        if i < len(jp_texts) and i < len(en_texts):
            jp_to_en.setdefault(jp_texts[i].split("\x0e")[0].strip(),
                                en_texts[i].split("\x0e")[0].strip())
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
