"""build_map_spots.py - the world-map catalogue for the World map page.

The save's `GmapSpotMgr` block holds one small record per map point (towns,
forts, caves, but also the invisible junctions and the intermediate points the
roads are drawn through).  Each record is keyed by `low32(fnv1_64(<internal
Japanese name>))`.  The names, their kind and their coordinates come from
`GameData/Gmap/Data.bin`:

    +0   header (7 bytes)
    +7   864 spot records, 17 bytes each:
         [u32 name offset][u8 kind][f32 x][f32 y][u32 extra]
    14693 717 road chains:
         [u16 n][n x u32 name offset][u16 n-1][(n-1) x 2 f32 midpoints]
         [u16 2(n-1)][2(n-1) x 4 f32 curve handles]
    ...  string pool: [u16 byte length][UTF-8], addressed by file offset

The table boundaries above are what this game build ships; the script checks
every invariant it relies on and stops if a different build breaks one.
English names come from `Msg/EUen/Spot.msbt.zst`, matched to the Japanese text
by label.  Writes map_spots.json:

    {"v": 1, "kinds": {...},
     "spots": [[hash8, jp, en, kind, x, y], ...],     # same order as the save
     "roads": [[spot index, ...], ...]}               # one list per road chain

Rebuild it for another game version:
    python build_map_spots.py <path to your dumped romfs folder>
(or set FEFW_ROM to it).
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fefw_core as core          # noqa: E402
import msbt                       # noqa: E402

ROM = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FEFW_ROM", "")

SPOTS_AT, SPOT_SIZE, SPOT_COUNT, CHAINS_AT, CHAIN_COUNT = 7, 17, 864, 14693, 717

# what each kind byte covers, read off the names that carry it
KINDS = {
    0: "Major city", 1: "Town", 2: "Temple", 3: "Station", 4: "Gate / fortress",
    5: "Landmark", 6: "Field / pass", 7: "Shrine / monument", 9: "Cave / mine",
    10: "Field / pass", 11: "Waypoint", 12: "Junction", 13: "Road point",
}
FIRST_HIDDEN_KIND = 11            # kinds >= 11 are the road network, not places

# internal-name prefixes of the unnamed network points -> English
GENERIC = [
    (r"^中スポット(\d+)$", "Waypoint {0}"),
    (r"^分岐点(\d+)$", "Junction {0}"),
    (r"^砂漠用分岐(\d+)$", "Desert junction {0}"),
    (r"^ソロモン用砂漠(\d+)$", "Desert point {0}"),
    (r"^リル海分岐(\d+)$", "Lir Sea junction {0}"),
    (r"^ダナン海分岐(\d+)$", "Danan Sea junction {0}"),
    (r"^イベント用(\d+)$", "Event point {0}"),
]


# spot names whose map spelling differs from the message text by a character
# (checked by label: same place, e.g. 廊 vs 廟, 峡谷 vs 渓谷)
LABELS = {
    "フォトナ神殿": "MID_Spot_TempleFotona",
    "ヘカトンケイル大要塞": "MID_Spot_Hecatoncheir",
    "コーエンの廊": "MID_Spot_CoenGallery",
    "叫獣峡谷": "MID_Spot_BeastGorge",
    "コロイオス砦跡": "MID_Spot_KoloiosFortress",
}


def string_at(d: bytes, off: int) -> str:
    n = struct.unpack_from("<H", d, off)[0]
    return d[off + 2:off + 2 + n].decode("utf-8")


def english(jp: str, names: dict) -> str:
    if jp in names:
        return names[jp]
    for pattern, fmt in GENERIC:
        m = re.match(pattern, jp)
        if m:
            return fmt.format(*(str(int(g)) for g in m.groups()))
    return ""


def main() -> int:
    data_bin = os.path.join(ROM, "GameData", "Gmap", "Data.bin")
    if not os.path.isfile(data_bin):
        print("usage: python build_map_spots.py <path to your dumped romfs folder>\n"
              "       (or set FEFW_ROM to it)")
        return 2
    d = open(data_bin, "rb").read()
    en_path = os.path.join(msbt.english_dir(os.path.join(ROM, "Msg")), "Spot.msbt.zst")
    names = msbt.jp_to_en(os.path.join(ROM, "Msg", "JPja", "Spot.msbt.zst"), en_path)
    en_text = msbt.read(en_path)
    names.update({jp: en_text[label] for jp, label in LABELS.items() if label in en_text})

    spots, index = [], {}
    for i in range(SPOT_COUNT):
        at = SPOTS_AT + SPOT_SIZE * i
        off, kind = struct.unpack_from("<IB", d, at)
        x, y = struct.unpack_from("<ff", d, at + 5)
        jp = string_at(d, off)
        if kind not in KINDS:
            raise SystemExit(f"{jp}: unknown kind {kind} - this build needs a look")
        h = "%08x" % core.id_hash(jp)
        if jp in index:
            raise SystemExit(f"duplicate spot name {jp}")
        index[jp] = i
        spots.append([h, jp, "", kind, round(x, 2), round(y, 2)])

    roads, p = [], CHAINS_AT
    for _ in range(CHAIN_COUNT):
        n = struct.unpack_from("<H", d, p)[0]
        offs = struct.unpack_from("<%dI" % n, d, p + 2)
        p += 2 + 4 * n
        mids = struct.unpack_from("<H", d, p)[0]
        p += 2 + 8 * mids
        curves = struct.unpack_from("<H", d, p)[0]
        p += 2 + 16 * curves
        if not (n >= 2 and mids == n - 1 and curves == 2 * mids):
            raise SystemExit("road table does not look like the one this script reads")
        roads.append([index[string_at(d, o)] for o in offs])
    pool = min(struct.unpack_from("<I", d, SPOTS_AT)[0], len(d))
    if p != pool:
        raise SystemExit(f"road table ends at {p}, string pool starts at {pool}")

    # English: the game's own text where it has one, otherwise built from the
    # parts of the internal name (road points are `<from>_<to>_<n>`)
    en_of = {}
    for s in spots:
        en_of[s[1]] = english(s[1], names)
    for s in spots:
        jp = s[1]
        en = en_of[jp]
        if not en and s[3] == 13:
            a, b, k = jp.rsplit("_", 2)
            en = f"Road: {en_of.get(a) or a} \u2192 {en_of.get(b) or b} ({k})"
        s[2] = en

    out = {"v": 1, "kinds": {str(k): v for k, v in KINDS.items()},
           "spots": spots, "roads": roads}
    path = os.path.join(HERE, "map_spots.json")
    with open(path, "w", encoding="utf8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    places = [s for s in spots if s[3] < FIRST_HIDDEN_KIND]
    print("%d spots (%d places, %d with an English name), %d roads -> %s"
          % (len(spots), len(places), sum(1 for s in places if s[2]), len(roads), path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
