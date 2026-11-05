"""
fefw_save.py — Fire Emblem: Fortune's Weave save slots (reader/writer).

Container (verified on real slots):

  0x000 u32 0xCDEFBCDD magic
  0x004 u32 0xE0       FNV window length
  0x008 u32 FNV-1a32(file[0x1F:0xFF])
  0x100 u32 len(file) - 0x104
  0x104 u32 0xCDEFBCDD
  0x108 u32 length of the zstd frame
  0x10C u32 FNV-1 over the DECOMPRESSED payload
  0x110 u32 3
  0x124 ... plain zstd frame to EOF

Unit records (verified by diffing Chapter_Ism_0_2 against Chapter_Ism_0_3 and
cross-checking the newest Auto slot):

  +0x00 u32  low 32 bits of FNV-1 64 (basis 0xCBF29CE484222325, prime
             0x100000001B3, multiply-then-xor) over the UTF-8 Person id
             ("PID_イシュマール", ...). This identifies the unit.
  +0x04 u32  per-instance salt
  +0x08 8 B  asset/instance ids
  ... 10-11 bytes of small fields ...
  s     9 x u16  stats  (Str, Mag, Dex, Spd, Lck, Def, Res, Cha, +1)
  s+18  (up to 4 zero bytes)
  b     u8 level
  b+1   u8 exp / exp-to-next
  b+2   u16 (class-ish, 16/17 for the party here)
  b+4   u8 0
  b+5   u32 max HP

The exact gap between the stat run and `b` varies by one byte between saves, so
`b` is located by the trailing signature rather than a fixed offset.
"""

from __future__ import annotations

import json
import os
import re
import struct

import zstandard

MAGIC = 0xCDEFBCDD
HDR_FNV_START = 0x1F
HDR_FNV_LEN = 0xE0
HERE = os.path.dirname(os.path.abspath(__file__))
ID_MAP_PATH = os.path.join(HERE, "unit_ids.json")
ITEM_MAP_PATH = os.path.join(HERE, "item_ids.json")

# The nine u16s are the game's stat block in the struct's own order, which a
# community cheat table exposes as `+8 Max Hp, +A Str, +C Mag, +E Dex, +10 Spd,
# +12 Lck, +14 Def, +16 Res, +18 Cha` (the save holds them as u16 pairs).  Slot 0
# is therefore the HP value and the trailing u32 after the level is the other
# half of the pair: in every record of every slot stats[0] <= that u32, so stats[0]
# is CURRENT HP and the u32 is MAX HP (the reverse of this editor's first guess).
STAT_NAMES = ["HP", "Str", "Mag", "Dex", "Spd", "Lck", "Def", "Res", "Cha"]


class SaveError(Exception):
    pass


# --------------------------------------------------------------------------
# job / class ids — the record's u32 at +0x04 is low32(FNV-1 64 of "JID_...")
# --------------------------------------------------------------------------
JOB_MAP_PATH = os.path.join(HERE, "job_ids.json")
_JOB_IDS: dict[int, dict] | None = None


def job_ids() -> dict[int, dict]:
    """hash -> {"jp": "JID_天翼兵", "en": "Wing Soldier"}."""
    global _JOB_IDS
    if _JOB_IDS is None:
        try:
            with open(JOB_MAP_PATH, encoding="utf8") as fh:
                raw = json.load(fh)
            _JOB_IDS = {int(k, 16): v for k, v in raw.items()}
        except Exception:
            _JOB_IDS = {}
    return _JOB_IDS


def job_name(value: int) -> str:
    meta = job_ids().get(value)
    if not meta:
        return f"unknown class {value:08x}"
    return meta.get("en") or meta.get("jp") or f"class {value:08x}"


# --------------------------------------------------------------------------
# hashes
# --------------------------------------------------------------------------
def fnv1a32(data: bytes, basis: int = 0x811C9DC5) -> int:
    h = basis
    for b in data:
        h = ((h ^ b) * 0x1000193) & 0xFFFFFFFF
    return h


def fnv1_32(data: bytes, basis: int = 0x811C9DC5) -> int:
    h = basis
    for b in data:
        h = ((h * 0x1000193) & 0xFFFFFFFF) ^ b
    return h


def fnv1_64(data: bytes, basis: int = 0xCBF29CE484222325) -> int:
    h = basis
    for b in data:
        h = ((h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF) ^ b
    return h


_UNIT_IDS: dict[int, dict] | None = None
_ITEM_IDS: dict[int, str] | None = None


ITEM_CATEGORIES = [
    ("weapon", ("sword", "lance", "spear", "axe", "bow", "blade", "katana", "dagger", "knuckle",
                "anima", "tome", "spell", "gauntlet", "剣", "槍", "斧", "弓", "刀", "拳", "書")),
    ("staff", ("staff", "杖")),
    ("consumable", ("vulnerary", "potion", "elixir", "medicine", "herb", "tonic", "薬", "傷薬")),
    ("accessory", ("ring", "bracelet", "charm", "ornament", "brooch", "necklace", "earring",
                   "crown", "tiara", "mask", "指輪", "腕輪", "守り", "飾り", "首飾り", "仮面", "冠")),
    ("shield", ("shield", "盾")),
]


WEAPON_TAIL = ("剣", "槍", "斧", "弓", "刀", "棍", "爪", "杖", "書", "盾", "鉾",
               "拳", "牙", "薙刀", "大剣", "魔弾", "魔輪")
ACCESSORY_WORDS = ("守り", "腕輪", "指輪", "首飾り", "飾り", "宝石", "珠", "護符", "鍔",
                   "amulat", "amulet", "ring", "bracelet", "charm")
CONSUMABLE_TAIL = ("薬", "草", "実", "果", "肉", "魚", "茶", "パン", "卵", "茸")


def item_category(meta: dict) -> str:
    """Best-effort type.  Deliberately conservative: an item is only a weapon
    when its name ENDS in a weapon noun, so accessories such as 妖刀の鍔
    ("demon-sword guard") are not offered for weapon slots."""
    jp = (meta.get("jp") or "")
    base = re.sub(r"＋[０-９0-9]+$", "", jp)
    en = (meta.get("en") or "").lower()
    en = re.sub(r"\s*\+\d+$", "", en)
    if any(w in jp.lower() for w in ACCESSORY_WORDS) or any(
            w in en for w in ("amulet", "ring", "bracelet", "charm")):
        return "accessory"
    if base.endswith(WEAPON_TAIL) or en.endswith(
            ("sword", "lance", "spear", "axe", "bow", "blade", "staff", "tome", "shield")):
        if any(w in jp for w in ("薬", "草")) or "book" in en and jp.endswith("書") and "の書" not in jp:
            return "consumable"
        return "weapon"
    if jp.endswith(CONSUMABLE_TAIL) or any(w in en for w in ("vulnerary", "medicine", "potion", "elixir")):
        return "consumable"
    if "書" in jp:
        return "consumable"
    return "misc"


def item_ids() -> dict[int, dict]:
    """low32(FNV-1 64 of "IID_…") -> {"jp": ..., "en": ...}."""
    global _ITEM_IDS
    if _ITEM_IDS is None:
        with open(ITEM_MAP_PATH, encoding="utf8") as fh:
            _ITEM_IDS = {int(k, 16): v for k, v in json.load(fh).items()}
    return _ITEM_IDS


_ASCII_ID = re.compile(r"[A-Za-z0-9_+\-. ]+$")


def is_shadow(meta: dict) -> bool:
    """True for internal/duplicate ids (WoodSword, H_WoodSword1, SecretBook).

    Item.bin stores every item twice: a Japanese id (the one the save actually
    uses) and an ASCII id used by the data pipeline.  Only the Japanese-named
    ids appear in game; writing an ASCII one into a slot shows nothing.
    """
    jp = (meta or {}).get("jp") or ""
    return bool(_ASCII_ID.fullmatch(jp))


def unit_ids() -> dict[int, dict]:
    global _UNIT_IDS
    if _UNIT_IDS is None:
        with open(ID_MAP_PATH, encoding="utf8") as fh:
            raw = json.load(fh)
        _UNIT_IDS = {int(k, 16): v for k, v in raw.items()}
    return _UNIT_IDS


# --------------------------------------------------------------------------
# container
# --------------------------------------------------------------------------
class SaveFile:
    def __init__(self, path: str | None = None, payload: bytes | None = None):
        self.path = path
        if path:
            with open(path, "rb") as fh:
                self.raw = fh.read()
        else:
            raise SaveError("need a path")
        if len(self.raw) < 0x124 or struct.unpack_from("<I", self.raw, 0)[0] != MAGIC:
            raise SaveError(f"{os.path.basename(path)}: not a Fortune's Weave slot")
        self.zstd_offset = self._zstd_offset()
        if payload is None:
            payload = zstandard.ZstdDecompressor().decompressobj().decompress(
                self.raw[self.zstd_offset:])
        self.payload = bytearray(payload)
        self.units: list[UnitRecord] = []
        self.scan()

    def _zstd_offset(self) -> int:
        i = self.raw.find(b"\x28\xb5\x2f\xfd")
        if i < 0:
            raise SaveError("no zstd frame")
        return i

    # -- checksums ------------------------------------------------------
    def header_ok(self) -> bool:
        window = struct.unpack_from("<I", self.raw, 4)[0] or HDR_FNV_LEN
        return struct.unpack_from("<I", self.raw, 8)[0] == \
            fnv1a32(self.raw[HDR_FNV_START:HDR_FNV_START + window])

    def payload_ok(self) -> bool:
        return struct.unpack_from("<I", self.raw, 0x10C)[0] == fnv1_32(bytes(self.payload))

    def verify(self) -> list[str]:
        out = []
        if not self.header_ok():
            out.append("header checksum mismatch")
        if not self.payload_ok():
            out.append("payload checksum mismatch")
        return out

    def to_bytes(self, level: int = 19) -> bytes:
        payload = bytes(self.payload)
        frame = zstandard.ZstdCompressor(level=level).compress(payload)
        out = bytearray(self.raw[:self.zstd_offset]) + frame
        struct.pack_into("<I", out, 0x100, len(out) - 0x104)
        struct.pack_into("<I", out, 0x104, MAGIC)
        struct.pack_into("<I", out, 0x108, len(out) - self.zstd_offset)
        struct.pack_into("<I", out, 0x10C, fnv1_32(payload))
        struct.pack_into("<I", out, 0x110, 3)
        window = struct.unpack_from("<I", out, 4)[0] or HDR_FNV_LEN
        struct.pack_into("<I", out, 8, fnv1a32(bytes(out[HDR_FNV_START:HDR_FNV_START + window])))
        return bytes(out)

    def save(self, path: str | None = None, backup: bool = True) -> str:
        path = path or self.path
        if not path:
            raise SaveError("no output path")
        if backup and os.path.exists(path):
            bak = path + ".bak"
            if not os.path.exists(bak) or os.path.getsize(bak) != os.path.getsize(path):
                with open(path, "rb") as src, open(bak, "wb") as dst:
                    dst.write(src.read())
        data = self.to_bytes()
        with open(path, "wb") as fh:
            fh.write(data)
        self.raw = data
        return path

    def scan(self) -> None:
        self.units = find_units(bytes(self.payload))

    def set_class(self, uid: int, new_hash: int) -> int:
        """Write a class id everywhere a unit stores it.

        The hash appears twice per unit block: the record header (+0x04) and a
        serialized section keyed by the class, so a half-written change would
        leave the two disagreeing.  Only occurrences of the *old* hash inside
        this unit's own block are touched, and both are replaced.
        """
        bases = sorted({r.base for r in self.units})
        pat_new = struct.pack("<I", int(new_hash) & 0xFFFFFFFF)
        n = 0
        for r in self.units:
            if r.uid != uid:
                continue
            old = struct.unpack_from("<I", self.payload, r.base + 4)[0]
            if old == (new_hash & 0xFFFFFFFF):
                continue
            end = next((b for b in bases if b > r.base), len(self.payload))
            pat_old = struct.pack("<I", old)
            i = self.payload.find(pat_old, r.base, end)
            while i >= 0:
                self.payload[i:i + 4] = pat_new
                n += 1
                i = self.payload.find(pat_old, i + 4, end)
            r.job_hash = new_hash & 0xFFFFFFFF
        return n



# --------------------------------------------------------------------------
# unit records
# --------------------------------------------------------------------------
class UnitRecord:
    __slots__ = ("base", "uid", "pid", "name", "stats_off", "level_off", "exp_off",
                 "hp_off", "class_off", "stats", "level", "exp", "max_hp", "klass",
                 "rank_offs", "skill_off", "job_hash", "hp_width")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def __repr__(self):
        return (f"<{self.name} lv{self.level} hp{self.max_hp} "
                f"stats={self.stats} @{self.base:#x}>")

    # -- writers (payload bytearray, in place) --------------------------
    def set_stat(self, i: int, value: int, payload: bytearray) -> None:
        struct.pack_into("<H", payload, self.stats_off + 2 * i, int(value) & 0xFFFF)

    def set_hp(self, value: int, payload: bytearray) -> None:
        """Write max HP in whichever width this copy stores it (4 / 2 / 1 byte)."""
        v = int(value) & 0xFFFFFFFF
        w = self.hp_width or 4
        if w == 4:
            struct.pack_into("<I", payload, self.hp_off, v)
        elif w == 2:
            struct.pack_into("<H", payload, self.hp_off, v & 0xFFFF)
        else:
            payload[self.hp_off] = v & 0xFF

    def set_level(self, value: int, payload: bytearray) -> None:
        payload[self.level_off] = int(value) & 0xFF

    def set_exp(self, value: int, payload: bytearray) -> None:
        payload[self.exp_off] = int(value) & 0xFF

    def ranks(self, payload: bytes) -> list[tuple[int, int, int]]:
        """(value offset, key, value) for the unit's weapon-rank table."""
        out = []
        for off, _k, _v in self.rank_offs:
            key = struct.unpack_from("<I", payload, off - 4)[0]
            val = struct.unpack_from("<I", payload, off)[0]
            out.append((off, key, val))
        return out

    # -- skill / aptitude table (right after current HP) ------------------
    def skills(self, payload: bytes) -> dict[int, tuple[int, int]]:
        """{skill key: (offset of the u16 value, value)} for this copy."""
        if self.skill_off is None:
            return {}
        return read_skills(payload, self.skill_off)

    def set_skill(self, key: int, value: int, payload: bytearray) -> bool:
        table = self.skills(bytes(payload))
        if key not in table:
            return False
        struct.pack_into("<H", payload, table[key][0], int(value) & 0xFFFF)
        return True

    def set_rank(self, value_off: int, value: int, payload: bytearray) -> None:
        struct.pack_into("<I", payload, value_off, int(value) & 0xFFFFFFFF)

    # -- class -----------------------------------------------------------
    def set_job(self, value: int, payload: bytearray) -> None:
        """Write the class id (the u32 right after the record id)."""
        struct.pack_into("<I", payload, self.base + 4, int(value) & 0xFFFFFFFF)
        self.job_hash = int(value) & 0xFFFFFFFF

    @property
    def job(self) -> str:
        return job_name(self.job_hash or 0)

    def item_slots(self, payload: bytes) -> list[tuple[int, int]]:
        """(offset, item id) pairs found around this record."""
        items = item_ids()
        out = []
        lo, hi = max(0, self.base - 0x60), min(len(payload) - 4, self.base + 0x180)
        for o in range(lo, hi):
            v = struct.unpack_from("<I", payload, o)[0]
            if v in items:
                out.append((o, v))
        return out


def find_units(payload: bytes) -> list[UnitRecord]:
    ids = unit_ids()
    jobs = job_ids()
    out: list[UnitRecord] = []
    n = len(payload)
    for o in range(0, n - 4):
        uid = struct.unpack_from("<I", payload, o)[0]
        meta = ids.get(uid)
        if meta is None:
            continue
        # a real record is followed by its class hash; template/definition
        # entries reuse the uid but hold something else there
        if jobs and struct.unpack_from("<I", payload, o + 4)[0] not in jobs:
            continue
        rec = _parse_record(payload, o, uid, meta)
        if rec:
            out.append(rec)
    return out


def _read_hp(payload: bytes, b: int) -> tuple[int, int]:
    """(value, width in bytes) for the HP field that follows the level byte."""
    hp = struct.unpack_from("<I", payload, b + 5)[0]
    if 5 <= hp <= 999:
        return hp, 4
    hp16 = struct.unpack_from("<H", payload, b + 5)[0]
    if 5 <= hp16 <= 999 and payload[b + 7] == 0 and payload[b + 8] == 0:
        return hp16, 2
    return payload[b + 5], 1


def _level_sig(payload: bytes, b: int) -> int | None:
    """Return HP if `b` looks like the level byte of a unit record.

    Two record variants exist in the same payload: most copies store current HP
    as u32, but the copy the game actually displays for some party members
    stores it as two u8s (current, max).  Rejecting the second form silently
    dropped that copy from the editor's unit list, so every edit missed the
    copy the game reads — the symptom is "I changed it and the game still shows
    the old value" for one character while others work.
    """
    if b + 9 > len(payload):
        return None
    if not (1 <= payload[b] <= 99) or payload[b + 4] != 0:
        return None
    hp = struct.unpack_from("<I", payload, b + 5)[0]
    if 5 <= hp <= 999:
        return hp
    hp16 = struct.unpack_from("<H", payload, b + 5)[0]
    if 5 <= hp16 <= 999 and payload[b + 7] == 0 and payload[b + 8] == 0:
        return hp16
    if 5 <= payload[b + 5] <= 255 and 5 <= payload[b + 6] <= 255:
        return payload[b + 5]
    return None

def _find_ranks(payload: bytes, base: int) -> list[tuple[int, int, int]]:
    """Locate the (key,value) rank table that follows a unit record.

    Layout: [u8 count][count x (u32 key, u32 value)].  Keys look like hashes,
    values stay small.
    """
    lo = base
    hi = min(len(payload) - 10, base + 0x220)
    best = []
    for i in range(lo, hi):
        n = payload[i]
        if not (2 <= n <= 12):
            continue
        if i + 1 + 8 * n > hi + 8:
            continue
        pairs = []
        ok = True
        for k in range(n):
            off = i + 1 + 8 * k
            key = struct.unpack_from("<I", payload, off)[0]
            val = struct.unpack_from("<I", payload, off + 4)[0]
            if not (0 < val <= 200) or key < 0x01000000:
                ok = False
                break
            pairs.append((off + 4, key, val))
        if ok and len(pairs) >= 2:
            if len(pairs) > len(best):
                best = pairs
    return best


def _make(payload: bytes, o: int, uid: int, meta: dict, s: int, b: int,
          vals) -> UnitRecord:
    hp, hp_w = _read_hp(payload, b)
    return UnitRecord(
        base=o, uid=uid, pid=meta["pid"], name=meta.get("name") or meta["pid"],
        stats_off=s, level_off=b, exp_off=b + 1, class_off=b + 2, hp_off=b + 5,
        stats=list(vals), level=payload[b], exp=payload[b + 1],
        klass=struct.unpack_from("<H", payload, b + 2)[0],
        max_hp=hp, hp_width=hp_w,
        rank_offs=_find_ranks(payload, o),
        skill_off=find_skills(payload, b + 5),
        job_hash=struct.unpack_from("<I", payload, o + 4)[0],
    )


def is_enemy(rec) -> bool:
    """Enemy/NPC units share the payload with the party (PID_EN_*)."""
    pid = getattr(rec, "pid", "") or ""
    return pid.startswith("PID_EN_") or pid.startswith("EN_")


# --------------------------------------------------------------------------
# skills / weapon aptitude
# --------------------------------------------------------------------------
# Right after the record's current-HP u32:
#
#   +0x00 u32  (link / offset, unused)
#   +0x04 u8   entry count
#   +0x08 n x { u8 skill key, u16 value }
#
# The value is CUMULATIVE skill experience, and the grade comes from a threshold
# ladder (not 100 per grade — writing 1100 displays as B+, which rules that out).
# The thresholds below are the Three Houses ladder, which is what Fortune's Weave
# reproduces; verified so far: 1100 -> B+ and 1260 -> B+.
GRADES = ["E", "E+", "D", "D+", "C", "C+", "B", "B+", "A", "A+", "S", "S+"]
SKILL_THRESHOLDS = [0, 40, 100, 180, 300, 460, 680, 960, 1320, 1760, 2520, 3600]

# keys 0-6 come from the data (carried weapons / unit type); 7-11 are confirmed
# by a community cheat table that lists the same struct in memory as a fixed
# 12-slot u16 array at record+0x36: sword, lance, axe, bow, fist, black, white,
# infantry, horse, armor, wing, flag.  Key 12 is an extra slot the save holds
# that the memory array does not have; it stays unnamed.
SKILL_NAMES = {
    0: "Swords", 1: "Lances", 2: "Axes", 3: "Bows", 4: "Fists",
    5: "Black Magic", 6: "White Magic",
    7: "Infantry", 8: "Riding", 9: "Heavy Armor", 10: "Flying",
    11: "Authority", 12: "skill 12",
}


def grade_of(value: int) -> int:
    """Grade index for a stored skill-experience value."""
    idx = 0
    for i, t in enumerate(SKILL_THRESHOLDS):
        if value >= t:
            idx = i
    return idx


def grade_label(value: int) -> str:
    return GRADES[grade_of(value)]


def next_threshold(value: int) -> int | None:
    idx = grade_of(value)
    return SKILL_THRESHOLDS[idx + 1] if idx + 1 < len(SKILL_THRESHOLDS) else None



def read_skills(payload: bytes, off: int) -> dict[int, tuple[int, int]]:
    """Parse the aptitude table whose count byte sits at `off`."""
    n = payload[off]
    out: dict[int, tuple[int, int]] = {}
    o = off + 1
    for _ in range(n):
        if o + 3 > len(payload):
            return {}
        key = payload[o]
        out[key] = (o + 1, struct.unpack_from("<H", payload, o + 1)[0])
        o += 3
    return out


def find_skills(payload: bytes, hp_off: int) -> int | None:
    """Offset of the aptitude count byte for a unit, or None.

    The table follows the record's current-HP u32 but the gap is one or two
    bytes wider on some copies, so several deltas are tried and the table with
    the most entries wins (a 1-entry false positive sits at delta 6 on some
    units and would otherwise hide the real 3-entry table).
    """
    best = None
    for delta in range(4, 24):
        off = hp_off + delta
        if off + 5 > len(payload):
            break
        n = payload[off]
        if not (1 <= n <= 13):
            continue
        o, keys, ok = off + 1, [], True
        for _ in range(n):
            if o + 3 > len(payload):
                ok = False
                break
            k = payload[o]
            v = struct.unpack_from("<H", payload, o + 1)[0]
            # real values are cumulative exp (S+ starts at 3600); the cap has to
            # stay above anything the editor can write or the table stops being
            # recognised after a write and every later edit silently misses.
            if v > 9999 or k > 13 or (keys and k <= keys[-1]):
                ok = False
                break
            keys.append(k)
            o += 3
        if not ok or not keys:
            continue
        score = (len(keys), 1 if delta == 8 else 0)
        if best is None or score > best[0]:
            best = (score, off)
    return best[1] if best else None


def pick_live(recs):
    """Pick the copy the game is actually using.

    A payload holds several snapshots of the same unit; the LAST snapshot in the
    file is the one written most recently, which is what the game loads.  Copies
    tie on level/exp, so ordering by offset is what breaks the tie (verified
    against the in-game inventory and the convoy list).
    """
    return max(recs, key=lambda r: (r.base, r.level, r.exp))


def _parse_record(payload: bytes, o: int, uid: int, meta: dict) -> UnitRecord | None:
    # pass 1: full record whose stat block carries real values.  Several two-byte
    # alignments of the same block can pass, so score them and take the densest.
    best = None
    for s in range(o + 0x0C, o + 0x30):
        if s + 18 + 10 > len(payload):
            break
        vals = struct.unpack_from("<9H", payload, s)
        if not all(v < 300 for v in vals):
            continue
        filled = sum(1 for v in vals if v >= 1)
        if filled < 5:
            continue
        for b in range(s + 18, s + 27):
            if not (0x28 <= b - o <= 0x40):
                continue
            if _level_sig(payload, b) is not None:
                cand = (filled, -s, s, b, vals)
                if best is None or cand[:2] > best[:2]:
                    best = cand
                break
    if best is not None:
        _, _, s, b, vals = best
        return _make(payload, o, uid, meta, s, b, vals)
    # pass 2: right structure, but the u32 that usually holds a HP-sized value
    # holds something else (seen: 1).  Class hash + level position + a skill
    # table immediately after the value are enough to call it a record, and
    # without this the copy the game actually reads is invisible to the editor.
    for b in range(max(o + 0x28, o + 0x10), min(o + 0x41, len(payload) - 12)):
        if not (1 <= payload[b] <= 99) or payload[b + 4] != 0:
            continue
        if find_skills(payload, b + 5) is None:
            continue
        for gap in (22, 23, 24, 21, 25, 20, 26, 19, 27):
            s = b - gap
            if s < o:
                continue
            vals = struct.unpack_from("<9H", payload, s)
            if all(v < 300 for v in vals):
                return _make(payload, o, uid, meta, s, b, vals)
    # pass 3: low-level recruits whose stat block is nearly all zeros.  A record
    # this small still carries its skill table right after the HP field, so use
    # that as the anchor instead of the stats.  Keep the window tight: a wider
    # scan latched onto the next structure and produced records with another
    # unit's level/HP (two "units" sharing one level offset).
    for b in range(max(o + 0x28, o + 0x10), min(o + 0x41, len(payload) - 12)):
        if _level_sig(payload, b) is None:
            continue
        if find_skills(payload, b + 5) is None:
            continue
        for gap in (22, 23, 24, 21, 25, 20, 26, 19, 27):
            s = b - gap
            if s < o:
                continue
            vals = struct.unpack_from("<9H", payload, s)
            if all(v < 300 for v in vals):
                return _make(payload, o, uid, meta, s, b, vals)
    return None


# --------------------------------------------------------------------------
# a whole save folder (Auto + every Chapter_* slot)
# --------------------------------------------------------------------------
SLOT_PREFIXES = ("Auto", "Chapter_", "Route_")


def is_slot_name(name: str) -> bool:
    """Slot files have no extension and never start with 'Auto.' etc."""
    if "." in name:
        return False
    return name == "Auto" or name.startswith(("Chapter_", "Route_"))


class SaveSet:
    """Every slot in one save folder, edited together.

    Slots: Auto, Chapter_<map>_<x>_<y> (battle state) and Route_<lord> (route /
    hub progress). The party lives in the Chapter_* and Route_* slots, so all of
    them have to carry the same edit.
    """

    def __init__(self, folder: str):
        self.folder = folder
        self.slots: list[SaveFile] = []
        for name in sorted(os.listdir(folder)):
            if not is_slot_name(name):
                continue
            p = os.path.join(folder, name)
            if not os.path.isfile(p):
                continue
            try:
                self.slots.append(SaveFile(p))
            except SaveError:
                continue
        if not self.slots:
            raise SaveError(f"no Auto/Chapter_* slot in {folder}")

    # -- inspection -----------------------------------------------------
    @staticmethod
    def live_copy(records):
        """The copy the game actually uses: highest level, then highest exp."""
        if not records:
            return None
        return max(records, key=lambda r: (r.level, r.exp))

    def best_slot(self) -> SaveFile | None:
        """Slot that actually carries unit records (hub saves carry none)."""
        cands = [sv for sv in self.slots if sv.units]
        if not cands:
            return None
        return max(cands, key=lambda sv: (len(sv.units), os.path.getmtime(sv.path)))

    def slot_report(self) -> str:
        return ", ".join(f"{os.path.basename(sv.path)} [{len(sv.units)}u]"
                         for sv in self.slots)

    def uids(self) -> list[int]:
        seen: list[int] = []
        for sv in self.slots:
            for u in sv.units:
                if u.uid not in seen:
                    seen.append(u.uid)
        return seen

    def records(self, uid: int) -> list[UnitRecord]:
        return [u for sv in self.slots for u in sv.units if u.uid == uid]

    def summary(self, uid: int) -> UnitRecord | None:
        return self.live_copy(self.records(uid))

    def slot_count(self, uid: int) -> tuple[int, int]:
        slots = sum(1 for sv in self.slots if any(u.uid == uid for u in sv.units))
        copies = sum(1 for sv in self.slots for u in sv.units if u.uid == uid)
        return slots, copies

    # -- edits ----------------------------------------------------------
    def _write(self, uid: int, fn) -> int:
        touched = 0
        for sv in self.slots:
            changed = False
            for u in sv.units:
                if u.uid == uid:
                    fn(u, sv)
                    changed = True
                    touched += 1
            if changed:
                sv.scan()          # offsets are stable, but keep the model fresh
        return touched

    def patch_stat(self, uid: int, i: int, value: int) -> int:
        return self._write(uid, lambda u, sv: u.set_stat(i, value, sv.payload))

    def patch_hp(self, uid: int, value: int) -> int:
        return self._write(uid, lambda u, sv: u.set_hp(value, sv.payload))

    def patch_level(self, uid: int, value: int) -> int:
        return self._write(uid, lambda u, sv: u.set_level(value, sv.payload))

    def patch_exp(self, uid: int, value: int) -> int:
        return self._write(uid, lambda u, sv: u.set_exp(value, sv.payload))

    # -- io -------------------------------------------------------------
    def write(self) -> list[str]:
        out = []
        for sv in self.slots:
            sv.save(sv.path)
            out.append(os.path.basename(sv.path))
        for sv in self.slots:
            sv.scan()
        return out

    def verify(self) -> list[str]:
        bad = []
        for sv in self.slots:
            for p in sv.verify():
                bad.append(f"{os.path.basename(sv.path)}: {p}")
        return bad


# --------------------------------------------------------------------------
# money (gold) — located once per save, then remembered by a byte signature
# --------------------------------------------------------------------------
MONEY_SIG_PATH = os.path.join(HERE, "money_sig.json")


def find_money_candidates(payload: bytes, value: int) -> list[int]:
    """Offsets where a u32 equals the amount the game shows."""
    pat = struct.pack("<I", value & 0xFFFFFFFF)
    out, i = [], payload.find(pat)
    while i >= 0:
        out.append(i)
        i = payload.find(pat, i + 1)
    return out


def money_signature(payload: bytes, off: int) -> dict:
    """Bytes around the money field, with the value itself masked out."""
    pre = bytes(payload[max(0, off - 8):off])
    post = bytes(payload[off + 4:off + 12])
    return {"pre": pre.hex(), "post": post.hex()}


def locate_money(payload: bytes, sig: dict) -> int | None:
    pre = bytes.fromhex(sig["pre"])
    post = bytes.fromhex(sig["post"])
    needle = pre + bytes(4) + post
    # walk every occurrence of the pre-bytes and verify the post-bytes
    i = payload.find(pre)
    while i >= 0:
        off = i + len(pre)
        if bytes(payload[off + 4:off + 4 + len(post)]) == post:
            return off
        i = payload.find(pre, i + 1)
    return None


def load_money_sig() -> dict | None:
    try:
        with open(MONEY_SIG_PATH, encoding="utf8") as fh:
            return json.load(fh)
    except Exception:
        return None


def save_money_sig(sig: dict) -> None:
    with open(MONEY_SIG_PATH, "w", encoding="utf8") as fh:
        json.dump(sig, fh)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def default_save_dir() -> str | None:
    title = "04007EF01F8AE000"
    roots = [os.path.expandvars(r"%APPDATA%\eden\nand\user\save"),
             os.path.expandvars(r"%APPDATA%\Eden\nand\user\save")]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, _f in os.walk(root):
            if os.path.basename(dirpath) == title:
                for d in dirnames:
                    cand = os.path.join(dirpath, d)
                    if os.path.exists(os.path.join(cand, "Auto")):
                        return cand
    return None


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Fortune's Weave save editor")
    ap.add_argument("target", nargs="?", help="save folder or single slot")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--set-stat", nargs=3, metavar=("UNIT", "STAT", "N"))
    ap.add_argument("--set-hp", nargs=2, metavar=("UNIT", "N"))
    ap.add_argument("--set-level", nargs=2, metavar=("UNIT", "N"))
    ap.add_argument("--set-exp", nargs=2, metavar=("UNIT", "N"))
    args = ap.parse_args(argv)

    target = args.target or default_save_dir()
    if not target or not os.path.exists(target):
        print("no save found")
        return 2
    if not os.path.isdir(target):
        target = os.path.dirname(target)

    svs = SaveSet(target)
    best = svs.best_slot()
    print("slots:", svs.slot_report())
    if best:
        print("unit data taken from:", os.path.basename(best.path))
    for sv in svs.slots:
        print(f"{os.path.basename(sv.path)}: {len(sv.raw)} B, payload {len(sv.payload)} B, "
              f"units {len(sv.units)}")
        print("  checksums:", sv.verify() or "OK")
    for uid in svs.uids():
        u = svs.summary(uid)
        slots, copies = svs.slot_count(uid)
        print(f"  {u.name:<18} lv {u.level:>3}  exp {u.exp:>3}  HP {u.max_hp:>3}  "
              f"class {u.klass:>2}  stats {u.stats}  ({slots} slots / {copies} copies)")

    def find_unit(token: str):
        for uid in svs.uids():
            u = svs.summary(uid)
            t = token.lower()
            if t in u.name.lower() or t in u.pid.lower():
                return uid
        return None

    changed = False
    for attr, fn in (("set_stat", None), ("set_hp", svs.patch_hp),
                     ("set_level", svs.patch_level), ("set_exp", svs.patch_exp)):
        arg = getattr(args, attr)
        if not arg:
            continue
        uid = find_unit(arg[0])
        if uid is None:
            print(f"unit {arg[0]!r} not found")
            return 3
        if attr == "set_stat":
            stat = arg[1]
            idx = STAT_NAMES.index(stat) if stat in STAT_NAMES else int(stat)
            n = svs.patch_stat(uid, idx, int(arg[2]))
        else:
            n = fn(uid, int(arg[1]))
        print(f"{arg[0]}: {attr} -> {arg[1:]} ({n} copies)")
        changed = True
    if changed:
        print("wrote", ", ".join(svs.write()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))



# ----------------------------------------------------------------- convoy
CONVOY_ANCHOR = b"\xd3\xad\x44\x76"
CONVOY_ENTRY = 7          # 0x41 tag, u32 item id, u16 pad


CONVOY_SIG = b"\x01\x31\x05\x01\x00"
ITEMS_CACHE = set()


def _items_cache():
    global ITEMS_CACHE
    if not ITEMS_CACHE:
        ITEMS_CACHE = set(item_ids())
    return ITEMS_CACHE
ITEMS_CACHE = set()


def _items_cache():
    global ITEMS_CACHE
    if not ITEMS_CACHE:
        ITEMS_CACHE = set(item_ids())
    return ITEMS_CACHE
CONVOY_TAGS = (0x41, 0x61)


def convoy_blocks(payload: bytes) -> list:
    """Every bag/convoy list: [(row offset, qty, item id)] rows, grouped.

    Rows are {u16 qty, tag in (0x41, 0x61), u32 item id} but they are NOT on a
    fixed stride in every save (padding bytes appear between rows), so each row
    is located by its signature and the scan resynchronises afterwards.
    """
    ids = _items_cache()
    ids = _items_cache()
    lists = []
    i = -1
    while True:
        i = payload.find(CONVOY_SIG, i + 1)
        if i < 0:
            break
        o = i + len(CONVOY_SIG) - 1      # first tag byte
        rows = []
        misses = 0
        while o < len(payload) - 6 and len(rows) < 999:
            t = payload[o]
            if t in CONVOY_TAGS:
                qty = struct.unpack_from("<H", payload, o - 2)[0] if o >= 2 else 0
                iid = struct.unpack_from("<I", payload, o + 1)[0]
                if 0 <= qty <= 999 and (qty or iid in ids):
                    rows.append((o, qty, iid))
                    o += CONVOY_ENTRY
                    misses = 0
                    continue
            o += 1
            misses += 1
            if misses > 24:
                break
        if rows:
            lists.append(rows)
    return lists


def convoy_entries(payload: bytes, block) -> list:
    return [(q, i) for _o, q, i in block]


def convoy_items(payload: bytes, block) -> list:
    return [i for _o, _q, i in block]


def add_convoy_item(payload: bytearray, item_id: int, blocks, qty: int = 1) -> int:
    """Append a stack after the last row of every list, keeping its padding."""
    n = 0
    for block in blocks:
        if item_id in [i for _o, _q, i in block]:
            continue
        last = block[-1][0]
        off = last + CONVOY_ENTRY
        while off + 7 < len(payload) and payload[off] != 0:
            off += 1
        if off + 7 >= len(payload):
            continue
        struct.pack_into("<H", payload, off - 2, max(1, int(qty)) & 0xFFFF)
        payload[off] = 0x41
        struct.pack_into("<I", payload, off + 1, item_id & 0xFFFFFFFF)
        block.append((off, max(1, int(qty)), item_id))
        n += 1
    return n


def set_convoy_row(payload: bytearray, row_off: int, item_id: int, qty: int = 1) -> None:
    struct.pack_into("<H", payload, row_off - 2, max(1, int(qty)) & 0xFFFF)
    payload[row_off] = 0x41
    struct.pack_into("<I", payload, row_off + 1, item_id & 0xFFFFFFFF)


def remove_convoy_item(payload: bytearray, start: int, count: int, index: int) -> bool:
    """Delete entry `index`, shifting later entries up and zeroing the last slot."""
    if not (0 <= index < count):
        return False
    for k in range(index, count - 1):
        src = start + CONVOY_ENTRY * (k + 1)
        dst = start + CONVOY_ENTRY * k
        payload[dst:dst + CONVOY_ENTRY] = payload[src:src + CONVOY_ENTRY]
    last = start + CONVOY_ENTRY * (count - 1)
    payload[last:last + CONVOY_ENTRY] = b"\x00" * CONVOY_ENTRY
    return True


# ---------------------------------------------------------------- materials
def _bag_hits(payload: bytes, ids) -> list:
    """Every {u16 qty, 0x41, u32 id} triple in the payload."""
    out = []
    for o in range(2, len(payload) - 6):
        if payload[o] != 0x41:
            continue
        qty = struct.unpack_from("<H", payload, o - 2)[0]
        if not (1 <= qty <= 999):
            continue
        iid = struct.unpack_from("<I", payload, o + 1)[0]
        if iid in ids:
            out.append((o - 2, qty, iid))
    return out


def material_clusters(payload: bytes, ids, skip=()) -> list:
    """Group bag rows into clusters; each cluster is (stride, [(off, qty, id)]).

    The game stores two bags with different record sizes, so the stride is
    measured per cluster (gcd of the gaps) instead of assumed.
    """
    hits = [h for h in _bag_hits(payload, ids)
            if not any(s <= h[0] < s + 8 * 200 for s in skip)]
    hits.sort()
    clusters = []
    for off, qty, iid in hits:
        if clusters and off - clusters[-1][-1][0] <= 0x400:
            clusters[-1].append((off, qty, iid))
        else:
            clusters.append([(off, qty, iid)])
    out = []
    for cl in clusters:
        if len(cl) < 2:
            continue
        gaps = [b[0] - a[0] for a, b in zip(cl, cl[1:])]
        stride = min(gaps)
        if stride < 6 or any(g % stride for g in gaps):
            continue
        out.append((stride, cl))
    return out


def material_set(payload: bytearray, off: int, qty: int, iid: int) -> None:
    struct.pack_into("<H", payload, off, max(1, qty) & 0xFFFF)
    payload[off + 2] = 0x41
    struct.pack_into("<I", payload, off + 3, iid & 0xFFFFFFFF)


def material_add(payload: bytearray, stride: int, entries, qty: int, iid: int) -> int:
    """Append a stack into the first all-zero slot after the last entry."""
    off = entries[-1][0] + stride
    if off + stride > len(payload):
        return 0
    if any(payload[off:off + stride]):
        return 0
    material_set(payload, off, qty, iid)
    return 1
