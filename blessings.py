"""Blessing EXP only; seven full-width identities and fixed-size writes.

No selection, Divine Sand, audience, deed or story flags are changed here.
The separate audiences module implements experimental first-audience edits.
The level preview is derived from data thresholds, not a stored level field.
See https://github.com/Destorino5/fefw-editor/blob/feature/part2-story/docs/blessings.md for evidence, Fortuna and game-validation limits.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct

import fefw_core as core

MAX_EXP = 65535  # Storage limit, not a verified gameplay recommendation.


class BlessingError(core.SaveError):
    pass


@dataclass(frozen=True)
class God:
    name: str
    key: str
    thresholds: tuple[int, int, int] | None

    @property
    def hash(self) -> int:
        return core.fnv1_64(self.key.encode("utf8"))


GODS = (
    God("Fortuna", "MIR_フォトナ", None),
    God("Mars", "MIR_マーズ", (25, 60, 120)),
    God("Credna", "MIR_クレール", (15, 40, 80)),
    God("Kalla", "MIR_カーラ", (20, 50, 100)),
    God("Jurah", "MIR_ジュラ", (25, 60, 120)),
    God("Smyrnos", "MIR_スミルノス", (25, 60, 120)),
    God("Aurora", "MIR_アウロラ", (20, 50, 100)),
)
BY_HASH = {god.hash: god for god in GODS}


@dataclass(frozen=True)
class Record:
    hash: int
    selected: int
    exp: int
    exp_offset: int


@dataclass(frozen=True)
class Table:
    start: int
    end: int
    divine_sand: int
    records: tuple[Record, ...]


def read(f: core.SaveFile) -> Table:
    """Identify one live direct-child object by full MIR hashes, not index.

    Require the observed version/count/size and all seven unique identities.
    Record order is allowed to differ. A second candidate, even malformed,
    makes identification ambiguous and therefore read-only.
    """
    blocks = [b for b in f.blocks if b.name == "GameUserData"]
    if len(blocks) != 1:
        raise BlessingError("No unique GameUserData block; blessing editing is disabled.")
    tree = f.tree()
    parent = tree.node_at(blocks[0].start)
    if parent < 0:
        raise BlessingError("Cannot identify the live blessing data.")
    signatures = {struct.pack("<Q", h) for h in BY_HASH}
    candidates = []
    for index, node in enumerate(tree.nodes):
        if node.parent == parent and not node.struct:
            # Nested/embedded older states can contain the same hashes. Only
            # direct record positions in a non-struct object identify this table.
            if any(node.start + 18 + 11 * i <= node.end and
                   bytes(f.payload[node.start + 10 + 11 * i:node.start + 18 + 11 * i])
                   in signatures for i in range(7)):
                candidates.append((index, node))
    if len(candidates) != 1:
        raise BlessingError("No unique seven-god blessing table; this save is read-only here.")
    index, node = candidates[0]
    p, at = f.payload, node.start
    if (node.struct or node.end - at != 88 or p[at + 4] != 2 or p[at + 9] != 7
            or any(n.parent == index for n in tree.nodes)):
        raise BlessingError("Unrecognised blessing layout; editing is disabled.")
    records = []
    for i in range(7):
        start = at + 10 + i * 11
        h, selected, exp = struct.unpack_from("<QBH", p, start)
        records.append(Record(h, selected, exp, start + 9))
    if {r.hash for r in records} != set(BY_HASH):
        raise BlessingError("Missing, duplicate or unknown blessing identity; editing is disabled.")
    return Table(at, node.end, f.u32(at + 5), tuple(records))


def level_preview(h: int, exp: int) -> int | None:
    """Data-derived level 0–3; Fortuna has no established EXP progression."""
    thresholds = BY_HASH[h].thresholds
    return sum(exp >= threshold for threshold in thresholds) if thresholds else None


def edited(f: core.SaveFile, edits: dict[int, int]) -> bytearray:
    """Return a copy with only the requested two-byte EXP fields changed."""
    for h, exp in edits.items():
        if type(h) is not int or h not in BY_HASH:
            raise BlessingError("Only the seven identified gods can be edited.")
        if type(exp) is not int or not 0 <= exp <= MAX_EXP:
            raise BlessingError("EXP must be a whole number from 0 to 65535.")
    table = read(f)  # Validate everything before any write, including a no-op.
    result = bytearray(f.payload)
    for record in table.records:
        if record.hash in edits:
            struct.pack_into("<H", result, record.exp_offset, edits[record.hash])
    return result
