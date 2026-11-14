"""fefw_core.py - the save-format engine.

Everything here works on the *decompressed payload* and edits it through the
save's own object tree, so records can grow or shrink (add a class, an item, a
support flag...) and every pointer is rewritten.  Nothing is written to disk
here; the caller packs with `SaveFile.to_bytes` (see fefw_save.py).

Layout recap
  0x000 u32 magic 0xCDEFBCDD (again at 0x104), 0x108 compressed size,
        0x10C fnv1_32(payload), 0x110 = 3 (zstd), payload from 0x124.
  payload: u32 at 0 -> [u8 version][ptr block table]; the block table is
  (u32 name hash, ptr start) pairs; each block starts with a ptr to its end.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

MAGIC = 0xCDEFBCDD

BLOCK_NAMES = [
    "Header", "GameSound", "GameSchedule", "GameUserData", "HubData",
    "GmapSpotMgr", "GmapTroopMgr", "GameGmapData", "GameRestartData",
    "SubquestData", "SideStoryData", "Calendar", "RecommendData", "Random",
    "UnitPool", "RidePool", "LegionPool", "Transporter", "HubSeq", "Data",
]

ROUTE_CODES = {1: "Kai", 2: "Dit", 3: "Seo", 4: "Led", 9: "Ism"}


# --------------------------------------------------------------------------
# hashing
# --------------------------------------------------------------------------
def fnv1_32(data: bytes) -> int:
    h = 0x811C9DC5
    for b in data:
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ b
    return h


def fnv1_64(data: bytes) -> int:
    h = 0xCBF29CE484222325
    for b in data:
        h = ((h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF) ^ b
    return h


def id_hash(key: str) -> int:
    return fnv1_64(key.encode("utf-8")) & 0xFFFFFFFF


def _ptr(v: int) -> int:
    return (v & 0xFFFFFF) - 32


class SaveError(Exception):
    pass


# --------------------------------------------------------------------------
# container / blocks
# --------------------------------------------------------------------------
@dataclass
class Block:
    name: str
    hash: int
    at: int      # where the (hash, ptr) pair sits in the block table
    start: int
    end: int


class SaveFile:
    """A decompressed payload plus its block table."""

    def __init__(self, payload: bytes | bytearray):
        self.payload = bytearray(payload)
        self.blocks: list[Block] = []
        self._parse_blocks()

    # -- primitives ------------------------------------------------------
    def u32(self, at: int) -> int:
        return struct.unpack_from("<I", self.payload, at)[0]

    def u16(self, at: int) -> int:
        return struct.unpack_from("<H", self.payload, at)[0]

    def ptr(self, at: int) -> int:
        return _ptr(self.u32(at))

    def put_u32(self, at: int, value: int) -> None:
        struct.pack_into("<I", self.payload, at, value & 0xFFFFFFFF)

    def put_u16(self, at: int, value: int) -> None:
        struct.pack_into("<H", self.payload, at, value & 0xFFFF)

    # -- structure -------------------------------------------------------
    def _parse_blocks(self) -> None:
        if len(self.payload) < 12:
            raise SaveError("payload too small")
        ver = self.u32(0)
        self.version = ver >> 24
        table = _ptr(ver)
        if table <= 0 or table >= len(self.payload):
            raise SaveError("no block table")
        names = {fnv1_32(n.encode()): n for n in BLOCK_NAMES}
        out = []
        i = table
        # the table sits at the END of the payload and lists every block
        while i + 8 <= len(self.payload):
            nh = self.u32(i)
            start = _ptr(self.u32(i + 4))
            if not (4 <= start < len(self.payload) - 4):
                i += 8
                continue
            end = _ptr(self.u32(start))
            if not (start < end <= len(self.payload)):
                i += 8
                continue
            out.append(Block(names.get(nh, "#%08X" % nh), nh, i, start, end))
            i += 8
        if not out:
            raise SaveError("empty block table")
        self.blocks = sorted(out, key=lambda b: b.start)

    def block(self, name: str) -> Block | None:
        for b in self.blocks:
            if b.name == name:
                return b
        return None

    def block_names(self) -> list[str]:
        return [b.name for b in self.blocks]

    # -- units -----------------------------------------------------------
    def units(self) -> list["SaveUnit"]:
        blk = self.block("UnitPool")
        if not blk:
            return []
        count = self.u16(blk.start + 6)
        at = blk.start + 8
        out = []
        for _ in range(count):
            if at >= blk.end:
                break
            u = SaveUnit.read(self, at)
            out.append(u)
            if u.end <= at:
                break
            at = u.end
        return out

    def unit_at(self, at: int) -> "SaveUnit":
        return SaveUnit.read(self, at)

    def copy(self) -> "SaveFile":
        f = SaveFile.__new__(SaveFile)
        f.payload = bytearray(self.payload)
        f.version = self.version
        f.blocks = [Block(b.name, b.hash, b.at, b.start, b.end) for b in self.blocks]
        return f

    def tree(self) -> "SaveTree":
        return SaveTree.read(self.payload)


# --------------------------------------------------------------------------
# the object tree (what makes resizing edits safe)
# --------------------------------------------------------------------------
@dataclass
class Node:
    start: int
    end: int
    struct: bool
    parent: int
    leaf: bool


@dataclass
class Ref:
    at: int
    target: int
    is_end: bool
    owner: int


LEAF_BLOCKS = {fnv1_32(b"Header"), fnv1_32(b"SubquestData")}


class SaveTree:
    def __init__(self, payload: bytearray):
        self.payload = payload
        self.nodes: list[Node] = []
        self.refs: list[Ref] = []
        starts, ends = [], []
        n = len(payload)
        for i in range(0, n - 84 + 1, 4):
            v = struct.unpack_from("<I", payload, i)[0]
            if v >> 24:
                continue
            p = _ptr(v)
            if p <= n and (p & 3) == 0 and self._is_unit(i, p):
                starts.append(i)
                ends.append(p)
        self._u_starts = starts
        self._u_ends = ends
        end = self._walk(0, n, -1)
        if end != n:
            raise SaveError("the save's objects end at 0x%X, not at the payload's "
                            "end (0x%X)" % (end, n))

    @staticmethod
    def read(payload: bytearray) -> "SaveTree":
        return SaveTree(payload)

    # -- helpers ---------------------------------------------------------
    def _u32(self, at: int) -> int:
        return struct.unpack_from("<I", self.payload, at)[0]

    def _is_unit(self, at: int, end: int) -> bool:
        p = self.payload
        if end - at < 84 or struct.unpack_from("<H", p, at + 4)[0] != 36:
            return False
        v = self._u32(at + 72)
        q = _ptr(v)
        return (v >> 24) == 0 and q > at + 76 and q + 8 <= end and (q & 3) == 0 \
            and self._u32(q) == 0xFFFFFFFF

    def _walk_unit(self, at: int, end: int, index: int) -> None:
        p = self._u32(at + 72)
        q = _ptr(p)
        self.nodes.append(Node(at + 72, q, False, index, True))
        self.refs.append(Ref(at + 72, q, True, len(self.nodes) - 1))
        cur = q + 8
        while cur + 4 <= end:
            v = self._u32(cur)
            t = _ptr(v)
            if (v >> 24) == 0 and cur + 4 <= t <= end and (t & 3) == 0:
                self.nodes.append(Node(cur, t, False, index, True))
                self.refs.append(Ref(cur, t, True, len(self.nodes) - 1))
                cur = t
                continue
            break

    @staticmethod
    def is_convoy(p: bytearray, at: int, end: int) -> bool:
        if end - at < 8 or p[at + 4] != 1:
            return False
        n = struct.unpack_from("<H", p, at + 5)[0]
        i = at + 7
        for _ in range(n):
            if i + 2 > end:
                return False
            q = struct.unpack_from("<H", p, i)[0]
            i += 2
            if q:
                if i >= end:
                    return False
                b = p[i]
                i += 5 if b == 65 else (13 if b == 97 else (end - i))
                if i > end:
                    return False
        return 0 <= end - i < 4

    def _crosses_unit(self, start: int, end: int) -> bool:
        import bisect
        i = bisect.bisect_left(self._u_starts, start + 1)
        while i < len(self._u_starts) and self._u_starts[i] < end:
            if self._u_ends[i] > end:
                return True
            i += 1
        i = bisect.bisect_left(self._u_starts, start)
        k = i - 1
        while k >= 0 and k >= i - 64:
            if self._u_starts[k] < start < self._u_ends[k] and self._u_ends[k] < end:
                return True
            k -= 1
        return False

    def _is_struct(self, at: int, limit: int) -> bool:
        v = self._u32(at)
        cnt = v >> 24
        base = _ptr(v)
        if not (1 <= cnt < 64) or base <= at or (base & 3) or base + 8 * cnt > limit:
            return False
        for i in range(cnt):
            m = self._u32(base + 8 * i + 4)
            t = _ptr(m)
            if (m >> 24) or t <= at or t >= base or (t & 3):
                return False
        return True

    @staticmethod
    def _is_embedded(p: bytearray, at: int, end: int) -> bool:
        if at + 12 <= end:
            v = struct.unpack_from("<I", p, at + 4)[0]
            if v != MAGIC:
                return struct.unpack_from("<I", p, at + 8)[0] == MAGIC
            return True
        return False

    @staticmethod
    def _is_map(p: bytearray, at: int, end: int) -> bool:
        if end - at < 12 or p[at + 4] != 0:
            return False
        n = struct.unpack_from("<H", p, at + 5)[0]
        i = at + 7
        for _ in range(n):
            i += 4
            if i >= end:
                return False
            i += 5 if p[i] == 0xFF else 1
        if n > 5:
            return 0 <= end - i <= 4
        return False

    def _scan(self, at: int, end: int, parent: int, members: dict | None) -> int:
        while at + 4 <= end:
            v = self._u32(at)
            t = _ptr(v)
            if members is not None and at in members:
                at = self._walk(at, end, parent, members[at] in LEAF_BLOCKS and parent == 0)
                continue
            bad = ((v >> 24) != 0 or t < at + 4 or t > end or (t & 3) != 0
                   or self._crosses_unit(at, t))
            if bad and ((v >> 24) == 0 or not self._is_struct(at, end)):
                at += 4
            else:
                at = self._walk(at, end, parent)
        return at

    def _walk(self, at: int, limit: int, parent: int, leaf_block: bool = False) -> int:
        if at & 3:
            raise SaveError("unaligned object at 0x%X" % at)
        v = self._u32(at)
        count = len(self.nodes)
        if v >> 24:
            cnt = v >> 24
            base = _ptr(v)
            if base + 8 * cnt > limit or base < at + 4:
                raise SaveError("bad struct at 0x%X" % at)
            self.nodes.append(Node(at, base + 8 * cnt, True, parent, False))
            self.refs.append(Ref(at, base, False, count))
            members: dict[int, int] = {}
            for i in range(cnt):
                m = _ptr(self._u32(base + 8 * i + 4))
                self.refs.append(Ref(base + 8 * i + 4, m, False, count))
                members.setdefault(m, self._u32(base + 8 * i))
            if self._scan(at + 4, base, count, members) != base:
                raise SaveError("the struct at 0x%X runs over its member table" % at)
            return base + 8 * cnt
        q = _ptr(v)
        if q < at + 4 or q > limit:
            raise SaveError("bad end pointer at 0x%X" % at)
        unit = self._is_unit(at, q)
        leaf = unit or leaf_block or self._is_embedded(self.payload, at, q) \
            or self._is_map(self.payload, at, q) or self.is_convoy(self.payload, at, q)
        self.nodes.append(Node(at, q, False, parent, leaf and not unit))
        self.refs.append(Ref(at, q, True, count))
        if unit:
            self._walk_unit(at, q, count)
        elif not leaf:
            self._scan(at + 4, q, count, None)
        return q

    # -- queries ---------------------------------------------------------
    def node_at(self, start: int) -> int:
        for i, n in enumerate(self.nodes):
            if n.start == start:
                return i
        return -1

    def innermost(self, frm: int, to: int) -> int:
        best = -1
        for i, n in enumerate(self.nodes):
            if n.start < frm and to <= n.end and (best < 0 or n.start >= self.nodes[best].start):
                best = i
        return best

    def _ancestor_or_self(self, node: int, of: int) -> bool:
        i = of
        while i >= 0:
            if i == node:
                return True
            i = self.nodes[i].parent
        return False

    # -- editing ---------------------------------------------------------
    def splice(self, owner: int, at: int, length: int, insert: bytes) -> bytearray:
        node = self.nodes[owner]
        delta = len(insert) - length
        stop = at + length
        if delta & 3:
            raise SaveError("the size change must be a multiple of 4")
        limit = _ptr(self._u32(node.start)) if node.struct else node.end
        if at < node.start + 4 or stop > limit:
            raise SaveError("the range is outside the object's content")
        for n in self.nodes:
            if (n.start < at < n.end < stop) or (at < n.start < stop < n.end):
                raise SaveError("the range cuts through the object at 0x%X" % n.start)
        old = self.payload
        new = bytearray(len(old) + delta)
        new[0:at] = old[0:at]
        new[at:at + len(insert)] = insert
        new[at + len(insert):] = old[stop:]
        for r in self.refs:
            if at <= r.at < stop:
                continue
            pos = r.at + delta if r.at >= stop else r.at
            target = r.target
            if at < target < stop:
                raise SaveError("the pointer at 0x%X points into the replaced range" % r.at)
            if target > stop or (target == stop and (not r.is_end or self._ancestor_or_self(r.owner, owner))):
                target += delta
            v = struct.unpack_from("<I", new, pos)[0]
            struct.pack_into("<I", new, pos, (v & 0xFF000000) | ((target + 32) & 0xFFFFFF))
        # read back: the same objects must exist
        check = SaveTree.read(new)

        def mapped(x: int) -> int:
            return x if x < stop else x + delta

        want = set()
        for i, n in enumerate(self.nodes):
            if n.start < at or n.start >= stop:
                end = n.end + delta if (n.end > stop or (n.end == stop and self._ancestor_or_self(i, owner))) else n.end
                want.add((mapped(n.start), end))
        have = {(n.start, n.end) for n in check.nodes}
        lost = want - have
        gained = {n for n in (have - want) if n[0] < at or n[1] > at + len(insert)}
        if lost or gained:
            msg = " ".join(["-0x%X..0x%X" % n for n in list(lost)[:3]]
                           + ["+0x%X..0x%X" % n for n in list(gained)[:3]])
            raise SaveError("the edited save didn't read back with the same objects; "
                            "nothing was changed (%s)" % msg)
        return new

    def copy_object(self, node: int, new_start: int) -> bytes:
        n = self.nodes[node]
        buf = bytearray(self.payload[n.start:n.end])
        shift = new_start - n.start
        for r in self.refs:
            if n.start <= r.at < n.end:
                if not (n.start <= r.target <= n.end):
                    raise SaveError("the object at 0x%X points outside itself (0x%X)"
                                    % (n.start, r.at))
                pos = r.at - n.start
                v = struct.unpack_from("<I", buf, pos)[0]
                struct.pack_into("<I", buf, pos,
                                 (v & 0xFF000000) | ((r.target + shift + 32) & 0xFFFFFF))
        return bytes(buf)


# --------------------------------------------------------------------------
# units
# --------------------------------------------------------------------------
@dataclass
class SaveUnit:
    start: int
    end: int
    flags: int
    person: int
    klass: int                 # current class id
    progress: bytes            # 9 bytes at +26 (unknown meaning)
    stats: list                # 9 s16 at +37 (points gained from level-ups)
    masteries: list            # [(mastery index, exp u16)]
    classes: list              # [(class id u32, value u8, flags u8)]
    items: list                # [item id u32]  (first section)
    skill_lists: list          # [[id, ...], ...] sections 1..n
    name: str | None = None
    look: bytes | None = None
    look_off: int = -1
    counters_off: int = -1
    counters: list = field(default_factory=list)

    @property
    def level_off(self) -> int:
        return self.start + 59

    @property
    def exp_off(self) -> int:
        return self.start + 60

    @property
    def hp_off(self) -> int:
        return self.start + 64

    @property
    def max_hp_off(self) -> int:
        return self.start + 66

    def stat_off(self, i: int) -> int:
        return self.start + 37 + i * 2

    def class_value_off(self, entry: int) -> int:
        return self.start + 77 + len(self.masteries) * 3 + 1 + entry * 6 + 4

    @classmethod
    def read(cls, f: SaveFile, at: int) -> "SaveUnit":
        p = f.payload
        end = f.ptr(at)
        flags = f.u16(at + 8)
        person = f.u32(at + 10)
        klass = f.u32(at + 14)
        progress = bytes(p[at + 26:at + 35])
        stats = [struct.unpack_from("<h", p, at + 37 + i * 2)[0] for i in range(9)]
        sec = f.ptr(at + 72)
        i = at + 76
        nm = p[i]
        i += 1
        masteries = []
        for _ in range(nm):
            masteries.append((p[i], struct.unpack_from("<H", p, i + 1)[0]))
            i += 3
        nc = p[i]
        i += 1
        nc = max(0, min(nc, (sec - i) // 6))
        classes = []
        for _ in range(nc):
            classes.append((f.u32(i), p[i + 4], p[i + 5]))
            i += 6
        items: list[int] = []
        skill_lists: list[list[int]] = []
        cur = sec + 8
        n = 0
        while cur + 4 <= end and n < 16:
            nxt = f.ptr(cur)
            if nxt <= cur or nxt > end:
                break
            found = []
            j = cur + 4
            while j + 5 <= nxt:
                b = p[j]
                if b in (65, 67, 97):
                    found.append(f.u32(j + 1))
                    j += 13 if b == 97 else 5
                else:
                    j += 1
            if n == 0:
                items = found
            else:
                skill_lists.append(found)
            cur = nxt
            n += 1
        name = None
        look = None
        look_off = -1
        counters_off = -1
        counters: list = []
        tail = tail_at(p, cur, end)
        if tail >= 0:
            i = tail + 4
            if p[i] == 3 and p[i + 3] == 7:
                ln = struct.unpack_from("<H", p, i + 1)[0] - 2
                name = bytes(p[i + 4:i + 4 + max(0, ln)]).decode("utf-8", "replace")
                i += 4 + max(0, ln) + 1
                look = bytes(p[i:i + 5])
                look_off = i
                i += 5
            else:
                i += 1
            i += 1
            cnt = p[i]
            i += 1
            counters_off = i
            for _ in range(cnt):
                if i + 8 > end:
                    break
                counters.append((f.u32(i), f.u32(i + 4)))
                i += 8
        return cls(start=at, end=end, flags=flags, person=person, klass=klass,
                   progress=progress, stats=stats, masteries=masteries,
                   classes=classes, items=items, skill_lists=skill_lists,
                   name=name, look=look, look_off=look_off,
                   counters_off=counters_off, counters=counters)


def tail_at(p: bytearray, frm: int, to: int) -> int:
    for i in range(to - 8, frm - 1, -1):
        if p[i] == 33 and p[i + 1] == 0 and p[i + 2] == 0 and p[i + 3] <= 16:
            if p[i + 4] == 0 and p[i + 5] == 5:
                return i
            if p[i + 4] == 3 and p[i + 7] == 7:
                ln = struct.unpack_from("<H", p, i + 5)[0]
                if ln >= 2 and i + 6 + ln + 6 <= to:
                    return i
    return -1


# --------------------------------------------------------------------------
# player (gold / renown / karma shards / difficulty)
# --------------------------------------------------------------------------
GOLD_AT = 6
RENOWN_AT = 10
KARMA_AT = 15


def user_data(f: SaveFile) -> int:
    """Offset of the GameUserData body (its first field), or -1."""
    b = f.block("GameUserData")
    if not b or b.start + 4 + 19 > len(f.payload) or f.payload[b.start + 4] != 23:
        return -1
    return b.start + 4


def read_settings(f: SaveFile):
    """(playthrough, difficulty, mode) from the Header, or None.

    The save keeps the pair as (mode, difficulty), in that order: the game's
    own GetMode() reads the byte before GetDifficulty().  Reading them the
    other way round made "Hard / Casual" land in game as "Normal / Classic".
    """
    p = f.payload
    if len(p) <= 16 or p[12] != 15:
        return None
    return (p[13], p[15], p[14])


# --------------------------------------------------------------------------
# edits
# --------------------------------------------------------------------------
@dataclass
class Item:
    id: int
    extra: bytes = b""      # 8 bytes for a forged copy
    magic: bool = False     # goes after the ordinary items

    def bytes(self) -> bytes:
        if self.extra:
            return b"\x61" + struct.pack("<I", self.id) + self.extra
        return b"\x41" + struct.pack("<I", self.id)


def sections(f: SaveFile, u: SaveUnit) -> list:
    out = []
    cur = f.ptr(u.start + 72) + 8
    n = 0
    while cur + 4 <= u.end and n < 16:
        nxt = f.ptr(cur)
        if nxt <= cur or nxt > u.end:
            break
        out.append(cur)
        cur = nxt
        n += 1
    return out


def unit_items(f: SaveFile, u: SaveUnit) -> list:
    p = f.payload
    secs = sections(f, u)
    if not secs:
        return []
    sec = secs[0]
    end = f.ptr(sec)
    nrm = p[sec + 5]
    mgc = p[sec + 6]
    i = sec + 7
    out = []
    for k in range(nrm + mgc):
        if i + 5 > end:
            break
        b = p[i]
        iid = struct.unpack_from("<I", p, i + 1)[0]
        if b not in (65, 97):
            raise SaveError("unknown item tag 0x%02X at 0x%X" % (b, i))
        extra = bytes(p[i + 5:i + 13]) if b == 97 else b""
        out.append(Item(iid, extra, k >= nrm))
        i += 5 + len(extra)
    return out


def skill_list(f: SaveFile, u: SaveUnit, index: int) -> list:
    p = f.payload
    secs = sections(f, u)
    if index >= len(secs):
        return []
    s = secs[index]
    n = struct.unpack_from("<H", p, s + 5)[0]
    return [struct.unpack_from("<I", p, s + 7 + i * 5 + 1)[0] for i in range(n)]


def replace_content(f: SaveFile, obj_start: int, body: bytes) -> bytearray:
    tr = SaveTree.read(f.payload)
    node = tr.node_at(obj_start)
    if node < 0:
        raise SaveError("no object at 0x%X" % obj_start)
    n = tr.nodes[node]
    if any(x.parent == node for x in tr.nodes):
        raise SaveError("the object holds other objects")
    b = bytearray(body)
    while len(b) & 3:
        b.append(0)
    return tr.splice(node, n.start + 4, n.end - n.start - 4, bytes(b))


def with_lists(f: SaveFile, u: SaveUnit, masteries, classes) -> bytearray:
    if len(masteries) > 255 or len(classes) > 255:
        raise SaveError("too many entries")
    b = bytearray([len(masteries) & 0xFF])
    for idx, exp in masteries:
        b.append(idx & 0xFF)
        b += struct.pack("<H", exp & 0xFFFF)
    b.append(len(classes) & 0xFF)
    for cid, value, flags in classes:
        b += struct.pack("<I", cid & 0xFFFFFFFF)
        b.append(value & 0xFF)
        b.append(flags & 0xFF)
    return replace_content(f, u.start + 72, bytes(b))


def with_items(f: SaveFile, u: SaveUnit, items) -> bytearray:
    secs = sections(f, u)
    if not secs:
        raise SaveError("the unit has no item section")
    nrm = [i for i in items if not i.magic]
    mgc = [i for i in items if i.magic]
    if len(nrm) > 255 or len(mgc) > 255:
        raise SaveError("too many items")
    b = bytearray([0, len(nrm), len(mgc)])
    for it in nrm + mgc:
        b += it.bytes()
    return replace_content(f, secs[0], bytes(b))


def with_skill_list(f: SaveFile, u: SaveUnit, index: int, ids) -> bytearray:
    secs = sections(f, u)
    if index >= len(secs):
        raise SaveError("no such skill list")
    b = bytearray([0]) + struct.pack("<H", len(ids))
    for i in ids:
        b += b"\x43" + struct.pack("<I", i & 0xFFFFFFFF)
    return replace_content(f, secs[index], bytes(b))


def set_u32(f: SaveFile, at: int, value: int) -> None:
    struct.pack_into("<I", f.payload, at, value & 0xFFFFFFFF)


def set_class(f: SaveFile, u: SaveUnit, cid: int) -> None:
    set_u32(f, u.start + 14, cid)


def set_mastery_exp(f: SaveFile, u: SaveUnit, entry: int, exp: int) -> None:
    struct.pack_into("<H", f.payload, u.start + 77 + entry * 3 + 1, exp & 0xFFFF)


def set_class_value(f: SaveFile, u: SaveUnit, entry: int, value: int) -> None:
    f.payload[u.start + 77 + len(u.masteries) * 3 + 1 + entry * 6 + 4] = value & 0xFF


# --------------------------------------------------------------------------
# convoy
# --------------------------------------------------------------------------
@dataclass
class Slot:
    qty: int
    item: "Item | None"


def convoy_at(f: SaveFile) -> int:
    blk = f.block("Transporter")
    if not blk:
        return -1
    for n in SaveTree.read(f.payload).nodes:
        if blk.start <= n.start and n.end <= blk.end \
                and SaveTree.is_convoy(f.payload, n.start, n.end):
            return n.start
    return -1


def convoy_read(f: SaveFile, at: int) -> list:
    p = f.payload
    n = struct.unpack_from("<H", p, at + 5)[0]
    i = at + 7
    out = []
    for _ in range(n):
        q = struct.unpack_from("<H", p, i)[0]
        i += 2
        if not q:
            out.append(Slot(0, None))
            continue
        b = p[i]
        if b not in (65, 97):
            raise SaveError("unknown convoy item tag 0x%02X at 0x%X" % (b, i))
        iid = struct.unpack_from("<I", p, i + 1)[0]
        extra = bytes(p[i + 5:i + 13]) if b == 97 else b""
        out.append(Slot(q, Item(iid, extra)))
        i += 5 + len(extra)
    return out


def convoy_write(f: SaveFile, at: int, slots) -> bytearray:
    b = bytearray([1]) + struct.pack("<H", len(slots))
    for s in slots:
        if not (0 <= s.qty <= 65535):
            raise SaveError("quantity out of range")
        b += struct.pack("<H", s.qty if s.item else 0)
        if s.qty and s.item:
            b += s.item.bytes()
    return replace_content(f, at, bytes(b))


# --------------------------------------------------------------------------
# mounts (rides) and battalions (legions)
# --------------------------------------------------------------------------
@dataclass
class Ride:
    id: int
    owner: int
    serial: int
    flag: int
    date: int
    name: str
    allies: bytes
    last: int

    def bytes(self) -> bytes:
        b = bytearray([6]) + struct.pack("<Q", self.id)
        b += bytes([self.owner, self.serial, 0, 0, self.flag])
        b += struct.pack("<I", self.date)
        name = self.name.encode("utf-8")
        if not name:
            b += b"\x00\x00"
        else:
            b += struct.pack("<H", len(name) + 2) + b"\x07" + name + b"\x00"
        b.append(len(self.allies) // 3)
        b += self.allies
        b += struct.pack("<H", self.last)
        return bytes(b)

    @staticmethod
    def read(p, at: int, end: int):
        if at + 18 > end or p[at] != 6:
            return None, at
        rid = struct.unpack_from("<Q", p, at + 1)[0]
        owner, serial, flag = p[at + 9], p[at + 10], p[at + 13]
        date = struct.unpack_from("<I", p, at + 14)[0]
        i = at + 18
        if i + 2 > end:
            return None, at
        ln = struct.unpack_from("<H", p, i)[0]
        i += 2
        name = ""
        if ln > 0:
            if ln < 2 or i + ln > end or p[i] != 7 or p[i + ln - 1] != 0:
                return None, at
            name = bytes(p[i + 1:i + ln - 1]).decode("utf-8", "replace")
            i += ln
        if i >= end:
            return None, at
        cnt = p[i]
        i += 1
        if i + cnt * 3 + 2 > end:
            return None, at
        allies = bytes(p[i:i + cnt * 3])
        i += cnt * 3
        last = struct.unpack_from("<H", p, i)[0]
        return Ride(rid, owner, serial, flag, date, name, allies, last), i + 2


@dataclass
class Legion:
    row: int
    owner: int
    id: int

    def bytes(self) -> bytes:
        b = bytearray(17)
        b[0], b[1], b[2] = 1, self.row, self.owner
        b[9:17] = struct.pack("<Q", self.id)
        return bytes(b)

    def __eq__(self, other):
        return isinstance(other, Legion) and \
            (self.row, self.owner, self.id) == (other.row, other.owner, other.id)


RIDE_CAPACITY = 200
LEGION_CAPACITY = 300


def _member(f: SaveFile, struct_at: int, hash_: int):
    v = f.u32(struct_at)
    base = _ptr(v)
    for i in range(v >> 24):
        if f.u32(base + i * 8) == hash_:
            return f.ptr(base + i * 8 + 4)
    return None


_CONVOY_M = 4022239793
_RIDE_M = 163182367
_LEGION_M = 1984212435


def party_store(f: SaveFile):
    """(convoy at, rides at, legions at) for the party, or None."""
    rb, lb = f.block("RidePool"), f.block("LegionPool")
    if not rb or not lb:
        return None
    r = _member(f, rb.start, _RIDE_M)
    if r is None:
        return None
    l = _member(f, lb.start, _LEGION_M)
    if l is None:
        return None
    return (convoy_at(f), r, l)


def rides(f: SaveFile, at: int) -> list:
    p = f.payload
    end = f.ptr(at)
    out = []
    if end - at <= 8:
        return out
    n = struct.unpack_from("<H", p, at + 5)[0]
    i = at + 7
    for _ in range(n):
        if i >= end:
            raise SaveError("the mount list at 0x%X ends early" % at)
        if p[i] == 0:
            i += 1
            continue
        r, i = Ride.read(p, i, end)
        if r is None:
            raise SaveError("unknown mount record at 0x%X" % i)
        out.append(r)
    return out


def legions(f: SaveFile, at: int) -> list:
    p = f.payload
    end = f.ptr(at)
    out = []
    if end - at <= 8:
        return out
    n = struct.unpack_from("<H", p, at + 5)[0]
    i = at + 7
    for _ in range(n):
        if i >= end:
            raise SaveError("the battalion list at 0x%X ends early" % at)
        if p[i] == 0:
            i += 1
            continue
        if p[i] != 1 or i + 17 > end:
            raise SaveError("unknown battalion record at 0x%X" % i)
        out.append(Legion(p[i + 1], p[i + 2], struct.unpack_from("<Q", p, i + 9)[0]))
        i += 17
    return out


def _replace_list(f: SaveFile, at: int, body: bytearray) -> bytearray:
    while len(body) & 3:
        body.append(0)
    tr = SaveTree.read(f.payload)
    node = tr.node_at(at)
    if node < 0:
        raise SaveError("no list at 0x%X" % at)
    n = tr.nodes[node]
    return tr.splice(node, n.start + 4, n.end - n.start - 4, bytes(body))


def with_rides(f: SaveFile, at: int, rs) -> bytearray:
    if len(rs) > RIDE_CAPACITY:
        raise SaveError("the mount list is full")
    b = bytearray([0]) + struct.pack("<H", RIDE_CAPACITY)
    for r in rs:
        b += r.bytes()
    b += bytes(RIDE_CAPACITY - len(rs))
    return _replace_list(f, at, b)


def with_legions(f: SaveFile, at: int, ls) -> bytearray:
    if len(ls) > LEGION_CAPACITY:
        raise SaveError("the battalion list is full")
    b = bytearray([0]) + struct.pack("<H", LEGION_CAPACITY)
    for l in ls:
        b += l.bytes()
    b += bytes(LEGION_CAPACITY - len(ls))
    return _replace_list(f, at, b)


# --------------------------------------------------------------------------
# the named flag store (GameUserData)
# --------------------------------------------------------------------------
@dataclass
class Flag:
    map: int
    hash: int
    offset: int      # where the value sits
    wide: bool       # 1 byte, or 0xFF marker + int32
    value: int


@dataclass
class FlagMap:
    index: int
    start: int
    flags: list


def flag_maps(f: SaveFile, known=None) -> list:
    """Every [u8 kind][u32 name][value] list in GameUserData."""
    blk = f.block("GameUserData")
    if not blk:
        return []
    p = f.payload
    out = []
    i = blk.start
    while i + 7 <= blk.end:
        if p[i + 4] != 0:
            i += 1
            continue
        end = f.ptr(i)
        n = f.u16(i + 5)
        if n == 0 or end <= i or end > blk.end:
            i += 1
            continue
        at = i + 7
        flags = []
        ok = True
        for _ in range(n):
            if at + 5 > end:
                ok = False
                break
            h = f.u32(at)
            kind = p[at + 4]
            if kind == 0xFF:
                if at + 9 > end:
                    ok = False
                    break
                flags.append(Flag(len(out), h, at + 5, True,
                                  struct.unpack_from("<i", p, at + 5)[0]))
                at += 9
            else:
                flags.append(Flag(len(out), h, at + 4, False, kind))
                at += 5
        if ok and 0 <= end - at <= 4:
            out.append(FlagMap(len(out), i, flags))
            i = at
        else:
            i += 1
    return out


def flag_bytes(fl: Flag, value: int) -> bytes:
    return struct.pack("<i", value) if fl.wide else bytes([value & 0xFF])


def flag_rebuild(f: SaveFile, fm: FlagMap, keep, extra: bytes = b"") -> bytearray:
    p = f.payload
    n = len(keep) + (1 if extra else 0)
    if n > 65535:
        raise SaveError("the map is full")
    b = bytearray([p[fm.start + 4]]) + struct.pack("<H", n)
    for fl in keep:
        start = fl.offset - 5 if fl.wide else fl.offset - 4
        b += p[start:start + (9 if fl.wide else 5)]
    b += extra
    return replace_content(f, fm.start, bytes(b))


def flag_add(f: SaveFile, fm: FlagMap, hash_: int, value: int) -> bytearray:
    if any(fl.hash == hash_ for fl in fm.flags):
        raise SaveError("the map already has this flag")
    b = bytearray(struct.pack("<I", hash_))
    if 0 <= value <= 254:
        b.append(value)
    else:
        b.append(0xFF)
        b += struct.pack("<i", value)
    return flag_rebuild(f, fm, fm.flags, bytes(b))


def flag_remove(f: SaveFile, fm: FlagMap, flag: Flag) -> bytearray:
    return flag_rebuild(f, fm, [x for x in fm.flags if x is not flag])


# --------------------------------------------------------------------------
# container write
# --------------------------------------------------------------------------
def fix_embedded_hashes(payload: bytearray) -> None:
    """Recompute the fnv1_32 of every embedded save whose body moved."""
    magic = struct.pack("<I", MAGIC)
    spots = []
    i = payload.find(magic)
    while i >= 0:
        spots.append(i)
        nxt = payload.find(magic, i + 4)
        i = nxt
    for at in sorted(spots, reverse=True):
        if at + 4 + 4 > len(payload):
            continue
        size = struct.unpack_from("<I", payload, at + 4)[0]
        if at + 32 + size <= len(payload) and \
                struct.unpack_from("<I", payload, at + 12)[0] == 1:
            h = fnv1_32(bytes(payload[at + 32:at + 32 + size]))
            struct.pack_into("<I", payload, at + 8, h)


def hashes_match(raw: bytes) -> bool:
    if struct.unpack_from("<I", raw, 8)[0] != fnv1_32(raw[32:256]):
        return False
    return struct.unpack_from("<I", raw, 268)[0] == fnv1_32(unpack(raw))


def unpack(raw: bytes) -> bytearray:
    import zstandard
    if len(raw) < 292 or struct.unpack_from("<I", raw, 0)[0] != MAGIC \
            or struct.unpack_from("<I", raw, 260)[0] != MAGIC:
        raise SaveError("not a Fortune's Weave save file")
    size = struct.unpack_from("<I", raw, 264)[0]
    body = raw[292:292 + min(size, len(raw) - 292)]
    if struct.unpack_from("<I", raw, 272)[0] != 3:
        return bytearray(body)
    return bytearray(zstandard.ZstdDecompressor().decompressobj().decompress(body))


def pack(original: bytes, payload: bytearray) -> bytes:
    import zstandard
    fix_embedded_hashes(payload)
    frame = zstandard.ZstdCompressor(level=12).compress(bytes(payload))
    out = bytearray(292 + len(frame))
    out[0:256] = original[0:256]
    st = read_settings(SaveFile(payload))
    if st and out[36] == 15:
        out[38] = st[2] & 0xFF          # mode first
        out[39] = st[1] & 0xFF          # then difficulty
    struct.pack_into("<I", out, 8, fnv1_32(bytes(out[32:256])))
    struct.pack_into("<I", out, 256, len(out) - 260)
    struct.pack_into("<I", out, 260, MAGIC)
    struct.pack_into("<I", out, 264, len(frame))
    struct.pack_into("<I", out, 268, fnv1_32(bytes(payload)))
    struct.pack_into("<I", out, 272, 3)
    out[292:] = frame
    return bytes(out)


# --------------------------------------------------------------------------
# units: look one up, copy one in, remove one, make a new one
# --------------------------------------------------------------------------
def unit_by_person(f: SaveFile, person: int, nth: int = 0) -> "SaveUnit | None":
    hits = [u for u in f.units() if u.person == (person & 0xFFFFFFFF)]
    return hits[nth] if nth < len(hits) else None


def copy_unit(src: SaveFile, unit: SaveUnit, dst: SaveFile,
              replace: int | None = None) -> bytearray:
    """Copy a unit record from one save into another (or over one in place)."""
    src_tree = SaveTree.read(src.payload)
    node = src_tree.node_at(unit.start)
    if node < 0:
        raise SaveError("the unit isn't an object of its own save")
    dst_tree = SaveTree.read(dst.payload)
    pool = dst.block("UnitPool")
    if pool is None:
        raise SaveError("no UnitPool in this save")
    owner = dst_tree.node_at(pool.start)
    units = dst.units()
    if replace is not None:
        if not (0 <= replace < len(units)):
            raise SaveError("no such unit")
        at = units[replace].start
        length = units[replace].end - units[replace].start
    else:
        at = units[-1].end if units else pool.start + 8
        length = 0
    new = dst_tree.splice(owner, at, length, src_tree.copy_object(node, at))
    if replace is None:
        struct.pack_into("<H", new, pool.start + 6, len(units) + 1)
    got = [x.person for x in SaveFile(new).units()]
    want = [x.person for x in units]
    if replace is None:
        want.append(unit.person)
    else:
        want[replace] = unit.person
    if got != want:
        raise SaveError("the copied unit didn't read back; nothing was changed")
    return new


def remove_unit(f: SaveFile, index: int) -> bytearray:
    """Delete a unit record, refusing if anything else still points at it."""
    tree = SaveTree.read(f.payload)
    pool = f.block("UnitPool")
    units = f.units()
    if pool is None or not (0 <= index < len(units)):
        raise SaveError("no such unit")
    u = units[index]
    for r in tree.refs:
        if (r.at < u.start or r.at >= u.end) and not r.is_end \
                and u.start <= r.target < u.end:
            raise SaveError("something else in the save points at this unit's "
                            "record (at 0x%X); nothing was removed" % r.at)
    owner = tree.node_at(pool.start)
    new = tree.splice(owner, u.start, u.end - u.start, b"")
    struct.pack_into("<H", new, pool.start + 6, len(units) - 1)
    if len(SaveFile(new).units()) != len(units) - 1:
        raise SaveError("the unit list didn't read back; nothing was removed")
    return new


def new_unit(f: SaveFile, template: SaveUnit, person: int, klass: int,
             level: int, hp: int, items=(), masteries=()) -> bytearray:
    """Grow a level-1 unit from a template record."""
    if template.name:
        raise SaveError("pick a template that isn't the player character")
    work = SaveFile(copy_unit(f, template, f))
    u = work.units()[-1]
    struct.pack_into("<I", work.payload, u.start + 10, person & 0xFFFFFFFF)
    struct.pack_into("<I", work.payload, u.start + 14, klass & 0xFFFFFFFF)
    work.payload[u.start + 26:u.start + 35] = bytes(9)
    work.payload[u.start + 37:u.start + 55] = bytes(18)
    level = max(1, min(99, int(level)))
    work.payload[u.start + 59] = level
    struct.pack_into("<H", work.payload, u.start + 60, (level - 1) * 100)
    struct.pack_into("<I", work.payload, u.start + 64, max(1, min(999, int(hp))))
    u = work.units()[-1]
    new = with_lists(work, u, list(masteries), [(klass & 0xFFFFFFFF, 0, 4)])
    work = SaveFile(new)
    u = work.units()[-1]
    return with_items(work, u, list(items))


# --------------------------------------------------------------------------
# mounts and battalions carried by a unit (its record's tail)
# --------------------------------------------------------------------------
@dataclass
class Gear:
    unit_number: int
    ride_at: int
    ride_len: int
    ride: "Ride | None"
    legion_at: int
    legion_len: int
    legion: "Legion | None"


def legion_ids(f: SaveFile) -> set:
    ids = set()
    st = party_store(f)
    if st:
        ids.update(l.id for l in legions(f, st[2]))
    rl = reliquary_store(f)
    if rl:
        ids.update(l.id for l in legions(f, rl[2]))
    return ids


def gear(f: SaveFile, u: SaveUnit) -> Gear | None:
    """The mount / battalion blob at the end of a unit record."""
    p = f.payload
    tail = tail_at(p, u.start, u.end)
    if tail < 0:
        return None
    base = tail - 10
    if base - 19 < u.start:
        return None
    legion = None
    known = legion_ids(f)
    if p[base - 17] == 1 and struct.unpack_from("<Q", p, base - 8)[0] in known:
        legion = Legion(p[base - 16], p[base - 15],
                        struct.unpack_from("<Q", p, base - 8)[0])
        at = base - 17
    else:
        if p[base - 1] != 0:
            return None
        at = base - 1
    number = p[tail - 9]
    if p[at - 1] == 0 and p[at - 2] == 35:
        return Gear(number, at - 1, 1, None, at, base - at, legion)
    i = at - 18
    while i > u.start and i > at - 400:
        if p[i] == 6 and p[i - 1] == 35:
            ride, nxt = Ride.read(p, i, at)
            if ride is not None and nxt == at:
                return Gear(number, i, at - i, ride, at, base - at, legion)
        i -= 1
    return None


def with_gear(f: SaveFile, u: SaveUnit, g: Gear, ride, legion) -> bytearray:
    p = f.payload
    body = bytearray(ride.bytes() if ride else b"\x00")
    body += legion.bytes() if legion else b"\x00"
    start = g.legion_at + g.legion_len
    body += p[start:u.end]
    while ((len(body) - (u.end - g.ride_at)) & 3) != 0:
        body.append(0)
    tr = SaveTree.read(p)
    node = tr.node_at(u.start)
    if node < 0:
        raise SaveError("the unit's record wasn't found")
    return tr.splice(node, g.ride_at, u.end - g.ride_at, bytes(body))


def reliquary_store(f: SaveFile):
    """The party's second store (convoy / rides / legions) inside GameUserData."""
    blk = f.block("GameUserData")
    if blk is None:
        return None
    outer = _member(f, blk.start, 2782227604)
    if outer is None:
        return None
    inner = _member(f, outer, 4225261395)
    if inner is None:
        return None
    tr = SaveTree.read(f.payload)
    node = tr.node_at(inner)
    if node < 0:
        return None
    for n in tr.nodes:
        if not n.struct or n.parent != node:
            continue
        c = _member(f, n.start, 4022239793)
        r = _member(f, n.start, _RIDE_M)
        l = _member(f, n.start, _LEGION_M)
        if c is not None and r is not None and l is not None:
            return (c, r, l)
    return None
