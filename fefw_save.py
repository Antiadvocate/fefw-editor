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
import sys
import unicodedata

import zstandard

MAGIC = 0xCDEFBCDD
HDR_FNV_START = 0x1F
HDR_FNV_LEN = 0xE0
HERE = os.path.dirname(os.path.abspath(__file__))
# Packaged as a single .exe (PyInstaller), the bundled id files are unpacked to a
# temporary folder that disappears on exit: read data from there, but keep
# anything the editor writes (settings, money_sig.json) next to the .exe.
FROZEN = bool(getattr(sys, "frozen", False))
DATA_DIR = getattr(sys, "_MEIPASS", HERE)
USER_DIR = os.path.dirname(os.path.abspath(sys.executable)) if FROZEN else HERE
ID_MAP_PATH = os.path.join(DATA_DIR, "unit_ids.json")
ITEM_MAP_PATH = os.path.join(DATA_DIR, "item_ids.json")

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
JOB_MAP_PATH = os.path.join(DATA_DIR, "job_ids.json")
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
        import fefw_core as core
        # embedded copies of the save live inside the payload: their own
        # checksums have to follow whatever moved
        core.fix_embedded_hashes(self.payload)
        payload = bytes(self.payload)
        frame = zstandard.ZstdCompressor(level=level).compress(payload)
        out = bytearray(self.raw[:self.zstd_offset]) + frame
        st = None
        try:
            st = core.read_settings(core.SaveFile(payload))
        except Exception:                     # noqa: BLE001 — keep the header as it was
            st = None
        if st and out[36] == 15:              # the load-screen summary
            out[38] = st[1] & 0xFF
            out[39] = st[2] & 0xFF
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
        # The .bak is the untouched original: it is written once and never
        # replaced, so it survives any number of later saves.  (Replacing it
        # whenever the size changed meant the second save overwrote the
        # original with the first edit.)
        if backup and os.path.exists(path):
            bak = path + ".bak"
            if not os.path.exists(bak):
                with open(path, "rb") as src, open(bak, "wb") as dst:
                    dst.write(src.read())
        data = self.to_bytes()
        # write next to the target and swap it in, so a crash mid-write never
        # leaves a half-written slot behind
        tmp = path + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
        self.raw = data
        return path

    def scan(self) -> None:
        self.units = find_units(bytes(self.payload))

    def set_class(self, uid: int, new_hash: int) -> int:
        """Point every copy of a unit at a class, adding it to its class list.

        A record is addressed at its person id, so the class id is the u32 at
        +4.  The previous version took *every* u32 in the block equal to that
        value and replaced it, which rewrote unrelated fields.  A class the unit
        does not own yet is appended to its class list first, the way the game
        does when a unit classes up.
        """
        import fefw_core as core
        uid = uid & 0xFFFFFFFF
        f = core.SaveFile(bytes(self.payload))
        u = next((x for x in f.units() if x.person == uid), None)
        if u is not None and not any(c[0] == (new_hash & 0xFFFFFFFF) for c in u.classes):
            self.payload = core.with_lists(
                f, u, u.masteries, list(u.classes) + [(new_hash & 0xFFFFFFFF, 0, 4)])
            self.scan()          # the record grew: every offset moved
        n = 0
        for r in self.units:
            if r.uid != uid:
                continue
            struct.pack_into("<I", self.payload, r.base + 4, new_hash & 0xFFFFFFFF)
            r.job_hash = new_hash & 0xFFFFFFFF
            r.klass = new_hash & 0xFFFFFFFF
            n += 1
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
        """EXP into the level (0-99); the save stores the running total."""
        lvl = max(1, int(self.level or 1))
        struct.pack_into("<H", payload, self.exp_off,
                         ((lvl - 1) * 100 + int(value)) & 0xFFFF)
        self.exp = int(value)

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

    def inventory(self, payload: bytes) -> "Inventory | None":
        """The unit's carried items and known spells, or None if not found."""
        return find_inventory(payload, self)


# --------------------------------------------------------------------------
# carried items / spells
# --------------------------------------------------------------------------
# After the class history every unit block holds (verified on real Auto and
# Route_* slots, three units, counts matching the game):
#
#   u32  section marker
#   u8   0
#   u8   number of carried items
#   u8   number of spells
#   entries, items first, then spells:
#     0x41  u32 item id                    (5 bytes)
#     0x61  u32 item id  + 8 bytes of data  (13 bytes; uses and the like)
#
# The editor used to treat every item id found near the record as a carried
# item, which pulled in the spell list and, for some units, the convoy that
# follows the record.
INV_ENTRY = {0x41: 5, 0x61: 13}


class Inventory:
    __slots__ = ("header", "items", "spells")

    def __init__(self, header: int, items: list, spells: list):
        self.header = header
        self.items = items      # [(offset of the u32 id, item id, tag)]
        self.spells = spells


def _parse_inventory(payload: bytes, h: int, ids) -> Inventory | None:
    if h + 7 > len(payload) or payload[h + 4] != 0:
        return None
    marker = struct.unpack_from("<I", payload, h)[0]
    if not (0 < marker < 0x01000000):
        return None
    n_items, n_spells = payload[h + 5], payload[h + 6]
    if n_items + n_spells == 0 or n_items > 32 or n_spells > 64:
        return None
    entries, o = [], h + 7
    for _ in range(n_items + n_spells):
        if o + 5 > len(payload):
            return None
        tag = payload[o]
        size = INV_ENTRY.get(tag)
        iid = struct.unpack_from("<I", payload, o + 1)[0]
        if size is None or iid not in ids:
            return None
        entries.append((o + 1, iid, tag))
        o += size
    return Inventory(h, entries[:n_items], entries[n_items:])


def find_inventory(payload: bytes, rec: "UnitRecord") -> Inventory | None:
    """Locate the item/spell lists that follow a unit record's class history."""
    if rec.skill_off is None:
        return None
    start = rec.skill_off + 1 + 3 * payload[rec.skill_off]
    ids = item_ids()
    for h in range(start, min(len(payload) - 7, start + 0x80)):
        inv = _parse_inventory(payload, h, ids)
        if inv is not None:
            return inv
    return None


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
    # level u8 at +59 (= b), exp u16 at +60 holding (level-1)*100 + exp into the
    # level, HP u32 at +64; the class id is the u32 right after the person id.
    lvl = payload[b]
    raw = struct.unpack_from("<H", payload, b + 1)[0]
    into = raw - (lvl - 1) * 100
    exp = into if 0 <= into <= 99 else (raw % 100)
    klass = struct.unpack_from("<I", payload, o + 4)[0]
    return UnitRecord(
        base=o, uid=uid, pid=meta["pid"], name=meta.get("name") or meta["pid"],
        stats_off=s, level_off=b, exp_off=b + 1, class_off=o + 4, hp_off=b + 5,
        stats=list(vals), level=lvl, exp=exp,
        klass=klass,
        max_hp=hp, hp_width=hp_w,
        rank_offs=_find_ranks(payload, o),
        skill_off=find_skills(payload, b + 5),
        job_hash=klass,
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
# The value is CUMULATIVE mastery experience, and the grade comes from this
# threshold ladder (S+ = 2560, confirmed in game).
GRADES = ["E", "E+", "D", "D+", "C", "C+", "B", "B+", "A", "A+", "S", "S+"]
SKILL_THRESHOLDS = [0, 20, 35, 80, 220, 440, 690, 910, 1215, 1510, 1960, 2560]

# The 13 weapon masteries, by the key the save stores.  (Earlier versions named
# keys 7-12 one place off: what they called "Riding" is Infantry, and so on.)
SKILL_NAMES = {
    0: "Swords", 1: "Lances", 2: "Axes", 3: "Bows", 4: "Fists",
    5: "Black Magic", 6: "White Magic", 7: "Special",
    8: "Infantry", 9: "Riding", 10: "Heavy Armor", 11: "Flying", 12: "Tactics",
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
            # real values are cumulative exp (S+ starts at 2560); the cap has to
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
MONEY_SIG_PATH = os.path.join(USER_DIR, "money_sig.json")

# Gold is read at a fixed position in the GameUserData block by fefw_layer /
# fefw_core (GameUserData + 6).  The bytes just before it are the route, part
# and chapter (e.g. 03 01 0c = Seo, part 1, chapter 12), so they can't be used
# to find it.  The search helpers below are kept only for old scripts.


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


def money_matches(payload: bytes, sig: dict) -> list[int]:
    """Every offset whose surrounding bytes match the remembered signature."""
    pre = bytes.fromhex(sig["pre"])
    post = bytes.fromhex(sig["post"])
    out, i = [], payload.find(pre)
    while i >= 0:
        off = i + len(pre)
        if bytes(payload[off + 4:off + 4 + len(post)]) == post:
            out.append(off)
        i = payload.find(pre, i + 1)
    return out


def locate_money(payload: bytes, sig: dict) -> int | None:
    """The gold offset, but only when the signature picks out exactly one spot.

    Gold has no decoded fixed position, so it is found by the bytes around it.
    If those bytes occur more than once the right one can't be told apart, and
    guessing could overwrite some other counter, so None is returned instead.
    """
    hits = money_matches(payload, sig)
    return hits[0] if len(hits) == 1 else None


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
def save_roots() -> list[str]:
    """Places the Eden emulator keeps its NAND saves (Windows and Linux)."""
    roots = []
    for var in ("APPDATA",):
        base = os.environ.get(var)
        if base:
            roots += [os.path.join(base, "eden", "nand", "user", "save"),
                      os.path.join(base, "Eden", "nand", "user", "save")]
    home = os.path.expanduser("~")
    roots += [os.path.join(home, ".local", "share", "eden", "nand", "user", "save"),
              os.path.join(home, "AppData", "Roaming", "eden", "nand", "user", "save")]
    seen, out = set(), []
    for r in roots:
        key = os.path.normcase(os.path.abspath(r))
        if key not in seen and os.path.isdir(r):
            seen.add(key)
            out.append(r)
    return out


def find_save_dirs() -> list[str]:
    """Every Fortune's Weave save folder found, most recently played first."""
    title = "04007EF01F8AE000"
    found = []
    for root in save_roots():
        for dirpath, dirnames, _f in os.walk(root):
            if os.path.basename(dirpath).upper() != title:
                continue
            for d in dirnames:
                cand = os.path.join(dirpath, d)
                auto = os.path.join(cand, "Auto")
                if os.path.exists(auto):
                    found.append((os.path.getmtime(auto), cand))
            dirnames[:] = []
    found.sort(reverse=True)
    return [p for _t, p in found]


def default_save_dir() -> str | None:
    dirs = find_save_dirs()
    return dirs[0] if dirs else None


# --------------------------------------------------------------------------
# display helpers
# --------------------------------------------------------------------------
ITEM_KINDS = ["Sword", "Lance", "Axe", "Bow", "Tome", "Staff", "Fist", "Shield",
              "Weapon", "Accessory", "Consumable", "Item"]

_KIND_WORDS = [
    ("Staff", ("staff", "rod", "wand"), ("杖",)),
    ("Sword", ("sword", "blade", "katana", "rapier", "sabre", "saber", "zanbato", "gladius"),
     ("剣", "刀")),
    ("Lance", ("lance", "spear", "javelin", "pike", "halberd", "trident"), ("槍", "鉾", "薙刀")),
    ("Axe", ("axe", "hatchet", "tomahawk", "poleax"), ("斧",)),
    ("Bow", ("bow", "longbow", "shortbow"), ("弓",)),
    ("Tome", ("tome", "magic book", "grimoire"), ("魔導書", "魔弾", "魔輪")),
    ("Fist", ("knuckle", "fist", "gauntlet", "claw", "cestus"), ("拳", "爪")),
    ("Shield", ("shield", "buckler"), ("盾",)),
]


def item_kind(meta: dict) -> str:
    """A finer, display-only type for an item (Sword, Lance, Tome, Accessory…).

    Built on top of item_category(), which stays the conservative check used to
    decide what may go into a slot; this one only picks a label and a colour.
    """
    cat = item_category(meta or {})
    if cat == "accessory":
        return "Accessory"
    if cat == "consumable":
        return "Consumable"
    jp = re.sub(r"＋[０-９0-9]+$", "", (meta or {}).get("jp") or "")
    en = re.sub(r"\s*\+\d+$", "", ((meta or {}).get("en") or "").lower())
    words = set(re.findall(r"[a-z]+", en))
    for kind, en_words, jp_tails in _KIND_WORDS:
        if any((" " in w and w in en) or w in words for w in en_words):
            return kind
        if jp.endswith(jp_tails):
            return kind
    if cat == "weapon":
        return "Tome" if jp.endswith("書") else "Weapon"
    return "Item"


def item_label(iid: int, meta: dict | None = None) -> str:
    """English name, with the forge level (+1, +2…) the Japanese name carries.

    Many English names drop it, so "Silver Axe" would otherwise appear four
    times in a list with nothing to tell the copies apart.
    """
    meta = item_ids().get(iid) if meta is None else meta
    if not meta:
        return f"unknown item {iid:08x}"
    en = unicodedata.normalize("NFKC", meta.get("en") or "").strip()
    jp = unicodedata.normalize("NFKC", meta.get("jp") or "").strip()
    m = re.search(r"\+(\d+)$", jp)
    base_jp = jp[:m.start()] if m else jp
    # forged copies take the base item's name, so "+1…+5" line up with it, and
    # half-translated names ("Poison 剣+1", "疾風 Sword") borrow a clean one
    if base_jp in _clean_names() and (m or not en or _CJK.search(en)):
        en = _clean_names()[base_jp]
    if not en:
        return jp or f"item {iid:08x}"
    en = re.sub(r"\s*\+\s*\d+$", "", en)
    return f"{en} +{m.group(1)}" if m else en


_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
_CLEAN: dict[str, str] | None = None


def _clean_names() -> dict[str, str]:
    """Japanese base name -> English name, for items whose English is complete."""
    global _CLEAN
    if _CLEAN is None:
        _CLEAN = {}
        forged: dict[str, str] = {}
        for meta in item_ids().values():
            jp = unicodedata.normalize("NFKC", meta.get("jp") or "").strip()
            en = unicodedata.normalize("NFKC", meta.get("en") or "").strip()
            if not (jp and en) or _CJK.search(en):
                continue
            m = re.search(r"\+(\d+)$", jp)
            if m:
                forged.setdefault(jp[:m.start()], re.sub(r"\s*\+\s*\d+$", "", en))
            else:
                _CLEAN.setdefault(jp, en)
        for jp, en in forged.items():
            _CLEAN.setdefault(jp, en)
    return _CLEAN


# ----------------------------------------------------------------- convoy
# The convoy is a fixed row of slots (verified on real Auto, Route_* and
# Chapter_* slots; every untouched list ends exactly where the next section's
# marker 31 82 be ef begins):
#
#   d3 ad 44 76  u32  u32  u32 0  u32      section header
#   01  u16 N                              N = number of slots (1329 so far)
#   N slots:
#     00 00                                empty slot (2 bytes)
#     u16 qty  41  u32 item id             item (7 bytes)
#     u16 qty  61  u32 item id  8 bytes    item with extra data (15 bytes)
#
# Materials (ore, meat, fish, plants, seals, maps) live in the same row, so a
# list holds far more than the weapons at its start.
#
# An empty slot and an item differ in size, so turning one into the other
# changes the length of everything after it.  The header holds position
# values that are not decoded yet, so the editor only makes size-preserving
# edits: change the item in an occupied slot (keeping its tag and extra data)
# or its quantity.  Writing a 7-byte item over empty slots, as older versions
# did for "Add", knocks every later slot out of line and the game can no
# longer read them.
CONVOY_ANCHOR = b"\xd3\xad\x44\x76"
CONVOY_END = b"\x31\x82\xbe\xef"
CONVOY_TAIL = {0x41: 4, 0x61: 12}     # bytes after the tag


class ConvoyRow:
    __slots__ = ("slot", "qty_off", "tag", "iid", "qty")

    def __init__(self, slot, qty_off, tag, iid, qty):
        self.slot, self.qty_off, self.tag, self.iid, self.qty = slot, qty_off, tag, iid, qty

    @property
    def id_off(self) -> int:
        return self.qty_off + 3


class Convoy:
    """One parsed convoy list.  `problem` is None for a list the game can read."""
    __slots__ = ("header", "slots", "rows", "end", "problem", "broken_slot")

    def __init__(self, header, slots, rows, end, problem=None, broken_slot=None):
        self.header, self.slots, self.rows, self.end = header, slots, rows, end
        self.problem, self.broken_slot = problem, broken_slot


def parse_convoy(payload: bytes, anchor: int) -> Convoy | None:
    """Parse the list whose section header starts at `anchor` (d3 ad 44 76)."""
    h = anchor + 20
    if h + 3 > len(payload) or payload[h] != 0x01:
        return None
    n = struct.unpack_from("<H", payload, h + 1)[0]
    if not 1 <= n <= 20000:
        return None
    ids = _items_cache()
    rows, o = [], h + 3
    for k in range(n):
        if o + 2 > len(payload):
            return Convoy(h, n, rows, o, "list runs past the end of the save", k)
        qty = struct.unpack_from("<H", payload, o)[0]
        if qty == 0:
            o += 2
            continue
        tag = payload[o + 2] if o + 2 < len(payload) else None
        tail = CONVOY_TAIL.get(tag)
        iid = struct.unpack_from("<I", payload, o + 3)[0] if o + 7 <= len(payload) else None
        if tail is None or iid not in ids:
            return Convoy(h, n, rows, o, f"slot {k + 1} of {n} can't be read — every item "
                                         "from there on is out of line", k)
        rows.append(ConvoyRow(k, o, tag, iid, qty))
        o += 3 + tail
    # (Lists holding a 0x61 item can end a byte short of the next section:
    # that item's extra data isn't fully decoded, so this is not checked.)
    return Convoy(h, n, rows, o)


def find_convoys(payload: bytes) -> list[Convoy]:
    """Every convoy list in a payload, in file order.  The last one is the live
    list; Auto also holds an earlier copy (the chapter-start snapshot)."""
    out, i = [], payload.find(CONVOY_ANCHOR)
    while i >= 0:
        c = parse_convoy(payload, i)
        if c is not None:
            out.append(c)
        i = payload.find(CONVOY_ANCHOR, i + 1)
    return out


def live_convoy(payload: bytes) -> Convoy | None:
    lists = find_convoys(payload)
    return lists[-1] if lists else None


def set_convoy_item(payload: bytearray, row: ConvoyRow, item_id: int) -> None:
    """Swap the item in an occupied slot.  The tag and any extra data stay, so
    the slot keeps its size."""
    struct.pack_into("<I", payload, row.id_off, item_id & 0xFFFFFFFF)
    row.iid = item_id & 0xFFFFFFFF


def set_convoy_qty(payload: bytearray, row: ConvoyRow, qty: int) -> None:
    """Change the quantity of an occupied slot (1 or more; 0 would make it an
    empty slot of a different size)."""
    qty = max(1, min(0xFFFF, int(qty)))
    struct.pack_into("<H", payload, row.qty_off, qty)
    row.qty = qty


_ITEMS_CACHE: set[int] = set()


def _items_cache() -> set[int]:
    global _ITEMS_CACHE
    if not _ITEMS_CACHE:
        _ITEMS_CACHE = set(item_ids())
    return _ITEMS_CACHE


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------
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
