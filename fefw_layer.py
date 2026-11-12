"""fefw_layer.py - the parts of fefw_save that guess, replaced by fefw_core.

`fefw_save` finds units, item slots, skills and the convoy by scanning the
payload for values that look right; that is why it reports "copies" of a unit,
loses a unit in some slots and refuses swaps it cannot place.  This module keeps
every public name of `fefw_save` (ids, labels, item catalogue, paths, file
defaults) but answers the structural questions from `fefw_core`, which reads the
save's own block table, unit pool and object tree.

`editor.py` imports from here instead of from `fefw_save`.
"""
from __future__ import annotations

import json
import os
import struct

import fefw_core as core
from fefw_save import *                      # noqa: F401,F403  (ids, labels, catalogue…)
from fefw_save import (                      # noqa: F401
    Convoy, ConvoyRow, SaveError, SaveFile as _SaveFile, UnitRecord as _UnitRecord,
    item_ids, item_label, is_enemy, unit_ids,
)

# --------------------------------------------------------------------------
# units
# --------------------------------------------------------------------------
def _meta(person: int) -> dict:
    meta = unit_ids().get(person & 0xFFFFFFFF)
    if meta:
        return meta
    return {"pid": "PID_%08X" % (person & 0xFFFFFFFF),
            "name": "unknown 0x%08X" % (person & 0xFFFFFFFF),
            "kind": "npc"}


_BASE_SLOTS = ("base", "uid", "pid", "name", "stats_off", "level_off", "exp_off",
               "hp_off", "class_off", "stats", "level", "exp", "max_hp", "klass",
               "rank_offs", "skill_off", "job_hash", "hp_width")


class UnitRecord(_UnitRecord):
    """One unit, straight out of the save's UnitPool.

    `fefw_save.UnitRecord.__init__` walks `self.__slots__`, which in a subclass
    is the subclass's tuple, so the fields are set here by name.
    """

    __slots__ = ("start", "classes", "masteries")

    def __init__(self, **kw):
        for k in _BASE_SLOTS:
            setattr(self, k, kw.get(k))
        self.start = kw.get("start", -1)
        self.classes = kw.get("classes") or []
        self.masteries = kw.get("masteries") or []

    @property
    def copies(self) -> int:
        return 1

    def inventory(self, payload):
        """Carried items from the record's first section (no scanning)."""
        from fefw_save import Inventory
        f = core.SaveFile(bytes(payload))
        u = unit_in(f, self.uid)
        if u is None:
            return None
        secs = core.sections(f, u)
        items = [(i, it.id, 1 if it.magic else 0)
                 for i, it in enumerate(core.unit_items(f, u))]
        return Inventory(secs[0] if secs else -1, items, [])


def _record(f: core.SaveFile, u: core.SaveUnit) -> UnitRecord:
    meta = _meta(u.person)
    lvl = f.payload[u.level_off]
    raw = f.u16(u.exp_off)
    into = raw - (lvl - 1) * 100
    rec = UnitRecord(base=u.start + 10, uid=u.person & 0xFFFFFFFF,
                     pid=meta["pid"], name=meta.get("name") or meta["pid"],
                     stats_off=u.start + 37, level_off=u.start + 59,
                     exp_off=u.start + 60, class_off=u.start + 14,
                     hp_off=u.start + 64, stats=list(u.stats), level=lvl,
                     exp=into if 0 <= into <= 99 else raw % 100,
                     klass=u.klass, max_hp=f.u16(u.hp_off), hp_width=4,
                     rank_offs=[], skill_off=0, job_hash=u.klass,
                     start=u.start, classes=list(u.classes),
                     masteries=list(u.masteries))
    return rec


def find_units(payload: bytes) -> list:
    f = core.SaveFile(bytes(payload))
    return [_record(f, u) for u in f.units()]


def pick_live(recs):
    """One record per unit now, but the callers still ask."""
    return max(recs, key=lambda r: (r.level, r.exp)) if recs else None


class SaveFile(_SaveFile):
    def scan(self) -> None:
        self.units = find_units(bytes(self.payload))


def core_of(payload) -> core.SaveFile:
    return core.SaveFile(bytes(payload))


def unit_in(f: core.SaveFile, uid: int):
    return next((u for u in f.units() if u.person == (uid & 0xFFFFFFFF)), None)


# --------------------------------------------------------------------------
# items
# --------------------------------------------------------------------------
def item_slots(payload, uid: int) -> list:
    """[(index, item id)] for the unit's carried items, in record order."""
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    if u is None:
        return []
    return [(i, it.id) for i, it in enumerate(core.unit_items(f, u))]


def set_item(payload: bytearray, uid: int, index: int, item_id: int) -> bool:
    """Swap one carried item; the record is rebuilt, so nothing shifts out of line."""
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    if u is None:
        return False
    items = core.unit_items(f, u)
    if not (0 <= index < len(items)):
        return False
    old = items[index]
    items[index] = core.Item(item_id & 0xFFFFFFFF, old.extra, old.magic)
    payload[:] = core.with_items(f, u, items)
    return True


def add_item(payload: bytearray, uid: int, item_id: int) -> bool:
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    if u is None:
        return False
    items = core.unit_items(f, u)
    if len(items) >= 255:
        return False
    payload[:] = core.with_items(f, u, items + [core.Item(item_id & 0xFFFFFFFF)])
    return True


def remove_item(payload: bytearray, uid: int, index: int) -> bool:
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    if u is None:
        return False
    items = core.unit_items(f, u)
    if not (0 <= index < len(items)):
        return False
    payload[:] = core.with_items(f, u, [x for i, x in enumerate(items) if i != index])
    return True


# --------------------------------------------------------------------------
# arts / skills  (the record's sections after the items)
# --------------------------------------------------------------------------
SKILL_LIST_NAMES = ("Equipped arts", "Equipped skills", "List 3", "Arts known",
                    "List 5", "Learned (all)")


def skill_lists(payload, uid: int) -> list:
    """[[id, …], …] for each skill list the unit has."""
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    if u is None:
        return []
    # section 0 is the item list; every section after it is a skill list
    return [core.skill_list(f, u, i) for i in range(1, len(core.sections(f, u)))]


def set_skill_list(payload: bytearray, uid: int, index: int, ids) -> bool:
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    if u is None:
        return False
    payload[:] = core.with_skill_list(f, u, index + 1, list(ids))
    return True


_SKILLS = None


def _skills() -> dict:
    global _SKILLS
    if _SKILLS is None:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "skill_ids.json"), encoding="utf8") as fh:
                _SKILLS = {int(k, 16): v for k, v in json.load(fh).items()}
        except Exception:                     # noqa: BLE001 — names are optional
            _SKILLS = {}
    return _SKILLS


def skill_label(sid: int) -> str:
    """English name, else the game's own Japanese name, else the id."""
    meta = item_ids().get(sid & 0xFFFFFFFF)
    if meta:
        return item_label(sid, meta)
    s = _skills().get(sid & 0xFFFFFFFF)
    if s:
        return s.get("en") or s.get("jp") or s.get("sid")
    return "0x%08X" % (sid & 0xFFFFFFFF)


# --------------------------------------------------------------------------
# convoy
# --------------------------------------------------------------------------
def live_convoy(payload) -> "Convoy | None":
    f = core.SaveFile(bytes(payload))
    at = core.convoy_at(f)
    if at < 0:
        return None
    p = f.payload
    slots = core.convoy_read(f, at)
    rows = []
    i = at + 7
    for k, s in enumerate(slots):
        qty_off = i
        i += 2
        if s.item is None:
            rows.append(ConvoyRow(k, qty_off, 0, 0, 0))
            continue
        rows.append(ConvoyRow(k, qty_off, p[qty_off + 2], s.item.id, s.qty))
        i += 5 + len(s.item.extra)
    c = Convoy.__new__(Convoy)
    c.header = at
    c.slots = len(slots)
    c.rows = rows
    c.end = f.ptr(at)
    c.problem = None
    c.broken_slot = -1
    return c


def damaged_convoy_at(payload) -> int:
    """Start of a convoy list that is there but can't be read, else -1.

    Older versions of this editor did "Add" by writing a 7-byte item over empty
    2-byte slots, which knocks every later slot out of line; the game then
    can't read those items.  Such a list keeps its header (01, slot count).
    """
    f = core.SaveFile(bytes(payload))
    if core.convoy_at(f) >= 0:
        return -1
    blk = f.block("Transporter")
    if not blk:
        return -1
    p = f.payload
    for n in core.SaveTree.read(p).nodes:
        if blk.start <= n.start and n.end <= blk.end and n.end - n.start > 8 \
                and p[n.start + 4] == 1 and 1 <= struct.unpack_from("<H", p, n.start + 5)[0] <= 20000:
            return n.start
    return -1


def salvage_convoy(payload) -> "tuple[int, list] | None":
    """(slot count, slots) rebuilt from a damaged list, or None.

    Reads the list slot by slot; where a slot can't be read (the list fell out
    of line), it steps one byte and tries again, which picks the rest of the
    items back up.  Empty slots are kept where they were found; if that makes
    the list longer than its slot count, empty slots are dropped from the end
    so every item survives.
    """
    at = damaged_convoy_at(payload)
    if at < 0:
        return None
    f = core.SaveFile(bytes(payload))
    p = f.payload
    n = struct.unpack_from("<H", p, at + 5)[0]
    end = f.ptr(at)
    ids = item_ids()
    out, i = [], at + 7
    while i + 2 <= end:
        q = struct.unpack_from("<H", p, i)[0]
        if q == 0:
            out.append(core.Slot(0, None))
            i += 2
            continue
        tag = p[i + 2] if i + 2 < end else None
        iid = struct.unpack_from("<I", p, i + 3)[0] if i + 7 <= end else None
        if tag in (0x41, 0x61) and iid in ids and q <= 999:
            extra = bytes(p[i + 7:i + 15]) if tag == 0x61 else b""
            out.append(core.Slot(q, core.Item(iid, extra)))
            i += 7 + len(extra)
        else:
            i += 1                       # out of line: step one byte and resync
    items = sum(1 for sl in out if sl.item)
    if items > n:
        return None
    while len(out) > n:                  # drop empty slots from the end first
        k = max(k for k, sl in enumerate(out) if not sl.item)
        out.pop(k)
    out += [core.Slot(0, None)] * (n - len(out))
    return n, out


def repair_convoy(payload: bytearray) -> int:
    """Rewrite a damaged list as a clean one.  Returns the items kept, or -1."""
    got = salvage_convoy(payload)
    if got is None:
        return -1
    _n, slots = got
    at = damaged_convoy_at(payload)
    f = core.SaveFile(bytes(payload))
    payload[:] = core.convoy_write(f, at, slots)
    return sum(1 for sl in slots if sl.item)


def convoy_rows(payload) -> list:
    c = live_convoy(payload)
    return c.rows if c else []


# The convoy is a fixed row of slots (1329 in every save seen), and the game
# keeps that count: a deposit fills an empty slot and a withdrawal empties one.
# So add and remove do the same, and the list's length never changes.  (The
# list is rebuilt and its pointers rewritten, so every later slot keeps its item.)
def add_convoy_slot(payload: bytearray, item_id: int, qty: int = 1) -> bool:
    """Put a stack into the first empty slot.  False if there is none."""
    f = core.SaveFile(bytes(payload))
    at = core.convoy_at(f)
    if at < 0:
        return False
    slots = core.convoy_read(f, at)
    free = next((k for k, sl in enumerate(slots) if not (sl.item and sl.qty)), None)
    if free is None:
        return False
    slots[free] = core.Slot(max(1, int(qty)), core.Item(item_id & 0xFFFFFFFF))
    payload[:] = core.convoy_write(f, at, slots)
    return True


# Forging/cooking materials sit in one run of Item.bin (and so of
# item_ids.json): ores from 錬成石 (Smithing Stone), then meat, fish, plants
# and leaves, ending with バウのフン (Bau Manure).  The two tutorial freebies
# (試供餌, 試供種) inside that run are left out.
_MAT_FIRST, _MAT_LAST = "錬成石", "バウのフン"
_MATERIALS: list | None = None


def material_ids() -> list:
    """Item ids of every forging/cooking material, in the game's order."""
    global _MATERIALS
    if _MATERIALS is None:
        out, inside = [], False
        for iid, meta in item_ids().items():
            jp = meta.get("jp") or ""
            inside = inside or jp == _MAT_FIRST
            if inside and not jp.startswith("試供"):
                out.append(iid)
            if jp == _MAT_LAST:
                break
        _MATERIALS = out if inside else []
    return _MATERIALS


def fill_materials(payload: bytearray, qty: int) -> "tuple[int, int, int]":
    """Every material to `qty`: stacks already in the convoy are set to it,
    missing ones go into empty slots the way a deposit does.  The slot count
    stays the same.  Returns (set, added, left out for lack of empty slots)."""
    f = core.SaveFile(bytes(payload))
    at = core.convoy_at(f)
    if at < 0:
        return 0, 0, 0
    qty = max(1, min(0xFFFF, int(qty)))
    slots = core.convoy_read(f, at)
    want = material_ids()
    have = {}
    for k, sl in enumerate(slots):
        if sl.item and sl.qty and sl.item.id in want:
            have.setdefault(sl.item.id, []).append(k)
    changed = 0
    for ks in have.values():
        for k in ks:
            if slots[k].qty != qty:
                slots[k] = core.Slot(qty, slots[k].item)
            changed += 1
    free = (k for k, sl in enumerate(slots) if not (sl.item and sl.qty))
    added = missed = 0
    for iid in want:
        if iid in have:
            continue
        k = next(free, None)
        if k is None:
            missed += 1
            continue
        slots[k] = core.Slot(qty, core.Item(iid))
        added += 1
    payload[:] = core.convoy_write(f, at, slots)
    return changed, added, missed


def remove_convoy_slot(payload: bytearray, slot: int) -> bool:
    """Empty one slot; the slots after it stay where they are."""
    f = core.SaveFile(bytes(payload))
    at = core.convoy_at(f)
    if at < 0:
        return False
    slots = core.convoy_read(f, at)
    if not (0 <= slot < len(slots)) or not slots[slot].item:
        return False
    slots[slot] = core.Slot(0, None)
    payload[:] = core.convoy_write(f, at, slots)
    return True


# --------------------------------------------------------------------------
# gold (fixed address: GameUserData + 6, in every slot)
# --------------------------------------------------------------------------
# GameUserData starts with the route, part and chapter the slot was saved in
# (e.g. 03 01 0c = Theodora's route, part 1, chapter 12).
ROUTE_LORDS = {1: "Cai", 2: "Dietrich", 3: "Theodora", 4: "Leda", 9: "Eshmel"}


def route_info(payload) -> "tuple[str, int, int] | None":
    """(lord, part, chapter) the slot was saved in, or None."""
    try:
        f = core.SaveFile(bytes(payload))
        ud = core.user_data(f)
    except Exception:                         # noqa: BLE001 — a label is optional
        return None
    if ud < 0:
        return None
    p = f.payload
    code = p[ud + 3]
    return ROUTE_LORDS.get(code, core.ROUTE_CODES.get(code, f"route {code}")), p[ud + 4], p[ud + 5]


def route_label(payload) -> str:
    info = route_info(payload)
    if not info:
        return ""
    lord, part, chapter = info
    return f"{lord} P{part} Ch{chapter}"


def current_gold(payload) -> "tuple[int, int] | None":
    f = core.SaveFile(bytes(payload))
    ud = core.user_data(f)
    if ud < 0:
        return None
    return f.u32(ud + core.GOLD_AT), ud + core.GOLD_AT


def set_gold(payload: bytearray, value: int) -> bool:
    f = core.SaveFile(bytes(payload))
    ud = core.user_data(f)
    if ud < 0:
        return False
    core.set_u32(f, ud + core.GOLD_AT, int(value))
    payload[:] = f.payload
    return True


def gold_offset(payload) -> int:
    cur = current_gold(payload)
    return cur[1] if cur else -1


# the amount-matching locator is gone: keep the names so old imports work
def find_money_candidates(payload, value) -> list:      # noqa: ARG001
    return []


def money_signature(payload, off):                      # noqa: ARG001
    return {}


def locate_money(payload, sig):                         # noqa: ARG001
    return gold_offset(payload) if gold_offset(payload) >= 0 else None


def money_matches(payload, sig):                        # noqa: ARG001
    return []


def load_money_sig() -> None:
    return None


def save_money_sig(sig) -> None:                        # noqa: ARG001
    return None


# --------------------------------------------------------------------------
# units: copy in, remove, mount / battalion
# --------------------------------------------------------------------------
def copy_unit_in(payload: bytearray, origin, uid: int) -> bool:
    """Copy a unit from another save file into this one."""
    dst = core.SaveFile(bytes(payload))
    src = core.SaveFile(core.unpack(open(origin, "rb").read()))
    u = unit_in(src, uid)
    if u is None:
        return False
    payload[:] = core.copy_unit(src, u, dst)
    return True


def remove_unit(payload: bytearray, uid: int) -> bool:
    f = core.SaveFile(bytes(payload))
    units = f.units()
    idx = next((i for i, u in enumerate(units) if u.person == (uid & 0xFFFFFFFF)), None)
    if idx is None:
        return False
    payload[:] = core.remove_unit(f, idx)
    return True


def unit_gear(payload, uid: int):
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    return core.gear(f, u) if u else None


def set_unit_gear(payload: bytearray, uid: int, ride, legion) -> bool:
    f = core.SaveFile(bytes(payload))
    u = unit_in(f, uid)
    if u is None:
        return False
    g = core.gear(f, u)
    if g is None:
        return False
    payload[:] = core.with_gear(f, u, g, ride, legion)
    return True


def battalions(payload) -> list:
    f = core.SaveFile(bytes(payload))
    st = core.party_store(f)
    return core.legions(f, st[2]) if st else []


def mounts(payload) -> list:
    f = core.SaveFile(bytes(payload))
    st = core.party_store(f)
    return core.rides(f, st[1]) if st else []


def add_battalion(payload: bytearray, legion) -> bool:
    f = core.SaveFile(bytes(payload))
    st = core.party_store(f)
    if not st:
        return False
    pool = core.legions(f, st[2])
    payload[:] = core.with_legions(f, st[2], pool + [legion])
    return True


def remove_battalion(payload: bytearray, index: int) -> bool:
    f = core.SaveFile(bytes(payload))
    st = core.party_store(f)
    if not st:
        return False
    pool = core.legions(f, st[2])
    if not (0 <= index < len(pool)):
        return False
    payload[:] = core.with_legions(f, st[2], [l for i, l in enumerate(pool) if i != index])
    return True
