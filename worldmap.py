"""worldmap.py - read and edit the world-map points in a save (`GmapSpotMgr`).

The block is a dictionary: for each of the game's map points (towns, forts,
caves, the invisible junctions and the intermediate points the roads are
drawn through) a `u32` key followed by a small object.  The key is
`low32(fnv1_64(<internal Japanese name>))`; the object's bytes are

    +0   u32   end pointer (never touched)
    +4   u8    state      1 = hidden, 3 = shown, 2 = seen on some roads (unresolved)
    +5   u8    secondary  meaning unknown (0 or 3 in real saves) - preserved
    +6   u8    visited    0 = dark icon, 1 = white icon
    ...        type-specific tail, preserved

The first key sits 5 bytes before its object, every later one 4 (a pad byte
follows the first).  The catalogue (`map_spots.json`, built by
`build_map_spots.py`) names every key, gives its kind and the road chains.

Only the state and visited bytes are ever written, in place, so no object is
resized and no pointer moves.  The layout and the behaviour of the two bytes
were worked out by Destorino5 in
https://github.com/Antiadvocate/fefw-editor/issues/27 and re-checked against
the editor's own saves.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import fefw_core as core

HERE = os.path.dirname(os.path.abspath(__file__))

HIDDEN, SHOWN = 1, 3
STATE_NAMES = {1: "Hidden", 2: "State 2", 3: "Shown"}
EDITABLE_SIZES = (12, 32, 40)       # record sizes seen in real saves
SECONDARY_SEEN = (0, 3)             # secondary-byte values seen in real saves
FIRST_NETWORK_KIND = 11             # kinds from here on are junctions / road points
ROAD_POINT_KIND = 13


class MapError(Exception):
    pass


# ----------------------------------------------------------------- catalogue
@dataclass(frozen=True)
class Spot:
    index: int
    key: int
    jp: str
    en: str
    kind: int
    x: float
    y: float

    @property
    def name(self) -> str:
        return self.en or self.jp

    @property
    def is_place(self) -> bool:
        return self.kind < FIRST_NETWORK_KIND


class Catalog:
    def __init__(self, raw: dict):
        self.kinds = {int(k): v for k, v in raw["kinds"].items()}
        self.spots = [Spot(i, int(h, 16), jp, en, kind, x, y)
                      for i, (h, jp, en, kind, x, y) in enumerate(raw["spots"])]
        self.by_key = {s.key: s for s in self.spots}
        self.roads: list[list[int]] = raw["roads"]

    def kind_name(self, kind: int) -> str:
        return self.kinds.get(kind, "Kind %d" % kind)

    def road_name(self, road: list[int]) -> str:
        a, b = self.spots[road[0]], self.spots[road[-1]]
        return "%s \u2192 %s" % (a.name, b.name)


_CATALOG: Catalog | None = None


def catalog() -> Catalog | None:
    """The baked map catalogue, or None when the data file is missing."""
    global _CATALOG
    if _CATALOG is None:
        try:
            with open(os.path.join(HERE, "map_spots.json"), encoding="utf8") as fh:
                _CATALOG = Catalog(json.load(fh))
        except (OSError, ValueError, KeyError):
            return None
    return _CATALOG


# --------------------------------------------------------------------- reading
@dataclass
class Record:
    spot: Spot
    at: int          # payload offset of the object (state is at+4)
    size: int
    state: int
    secondary: int
    visited: int

    @property
    def editable(self) -> bool:
        return self.size in EDITABLE_SIZES and self.secondary in SECONDARY_SEEN


def read(f: core.SaveFile) -> dict[int, Record]:
    """{key: Record} for every catalogued point the save holds.

    Refuses (MapError) when the block does not look like the layout this was
    written for, rather than guessing at offsets.
    """
    cat = catalog()
    if cat is None:
        raise MapError("map_spots.json is missing, so the map points can't be named.")
    block = f.block("GmapSpotMgr")
    if block is None:
        raise MapError("This save has no world-map block.")
    tree = f.tree()
    root = next((i for i, n in enumerate(tree.nodes) if n.start == block.start), -1)
    if root < 0:
        raise MapError("Couldn't find the world-map block in the save's object tree.")
    out: dict[int, Record] = {}
    for i, node in enumerate(n for n in tree.nodes if n.parent == root):
        at = node.start - (5 if i == 0 else 4)
        size = node.end - node.start
        if at < block.start or node.end > block.end or size < 8:
            raise MapError("Unexpected world-map block boundaries.")
        key = f.u32(at)
        if key in out:
            raise MapError("Duplicate world-map key - the layout isn't the expected one.")
        spot = cat.by_key.get(key)
        if spot is None:
            continue                      # a point this catalogue doesn't know: leave it
        p = f.payload
        out[key] = Record(spot, node.start, size, p[node.start + 4],
                          p[node.start + 5], p[node.start + 6])
    if len(out) < len(cat.spots) // 2:
        raise MapError("This save's map points don't match the catalogue "
                       "(%d of %d found) - another game version?" % (len(out), len(cat.spots)))
    return out


# --------------------------------------------------------------------- editing
def apply(f: core.SaveFile, edits: dict[int, tuple]) -> tuple[int, int]:
    """Patch `f.payload` in place.  `edits` = {key: (state, visited)} where
    either may be None to leave it.  Returns (changed bytes, skipped points).

    A point is skipped (never half-edited) when its record is an untested size
    or has a secondary byte other than 0 / 3, or when the byte to overwrite
    holds a value nobody has seen the game write.
    """
    before = bytes(f.payload)
    recs = read(f)
    changed = skipped = 0
    for key, (state, visited) in edits.items():
        rec = recs.get(key)
        if rec is None:
            continue
        if not rec.editable:
            skipped += 1
            continue
        writes = []
        if state is not None:
            if state not in (HIDDEN, SHOWN) or rec.state not in (HIDDEN, 2, SHOWN):
                skipped += 1
                continue
            writes.append((rec.at + 4, state))
        if visited is not None:
            if visited not in (0, 1) or rec.visited not in (0, 1):
                skipped += 1
                continue
            writes.append((rec.at + 6, visited))
        for at, value in writes:
            if f.payload[at] != value:
                f.payload[at] = value
                changed += 1
    block = f.block("GmapSpotMgr")
    lo, hi = block.start, block.end          # read() already proved it exists
    after = f.payload
    assert len(after) == len(before)
    assert all(lo <= i < hi for i in range(len(after)) if after[i] != before[i])
    return changed, skipped


# ------------------------------------------------------------------ selections
def places(cat: Catalog) -> list[Spot]:
    return [s for s in cat.spots if s.is_place]


def network(cat: Catalog) -> list[Spot]:
    return [s for s in cat.spots if not s.is_place]


def road_points(cat: Catalog, road: list[int], whole: bool) -> list[Spot]:
    """The points of a road chain: every one (to show it) or only the
    road's own points (to hide it without touching towns and shared junctions)."""
    spots = [cat.spots[i] for i in road]
    return spots if whole else [s for s in spots if s.kind == ROAD_POINT_KIND]
