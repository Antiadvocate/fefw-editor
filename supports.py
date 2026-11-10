"""
Support chart and point table for Fire Emblem: Fortune's Weave.

Three separate things live here:

* **The pair chart** — every support pair the game data defines, with the
  highest rank each pair can reach (C / B / A / S).  This comes from
  ``GameData/Reliance.bin`` and the ``支援会話_<A>_<B>_<rank>`` flag names, and
  is baked into ``supports.json`` so the editor needs no ROM access.

* **Conversation flags** — the save records ``支援会話_<A>_<B>_<rank>`` as an
  ordinary flag once that conversation has been seen, so the editor can show
  which of a pair's conversations this save has registered.

* **Support points** — the save holds a sparse table of 12-byte entries,
  ``[u32 pair hash][u32 points][u32 extra]``, inside ``GameUserData``.  The game
  derives the support *level* from the point value; 3200 is the maximum
  (level 5).  The pair hashes are precomputed constants — no formula maps
  character ids to them — so the whole 2628-pair table is baked into
  ``support_points.json``.

  The layout, the way the table is located and the write recipe come from
  https://github.com/Antiadvocate/fefw-editor/issues/19 (wingoflan).  The table
  does not start at a fixed offset, so it is found by looking for the entries
  themselves; only the ``points`` word is ever written, ``extra`` is left alone.
"""

from __future__ import annotations

import json
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "supports.json")
POINTS_PATH = os.path.join(HERE, "support_points.json")
RANKS = ("C", "B", "A", "S")

MAX_POINTS = 3200       # the maximum; confirmed in-game to be level 5
ENTRY_SIZE = 12         # [u32 pair hash][u32 points][u32 extra]

_pairs: list[dict] | None = None
_by_char: dict[str, dict] | None = None
_points: dict | None = None
_known: set[int] | None = None
_partners: dict[str, list[dict]] | None = None


def pairs() -> list[dict]:
    global _pairs
    if _pairs is None:
        try:
            with open(DATA_PATH, encoding="utf-8") as fh:
                _pairs = list(json.load(fh).get("pairs", []))
        except (OSError, ValueError):
            _pairs = []
    return _pairs


def by_char() -> dict[str, dict]:
    """jp name -> {jp, en, partners:[{jp, en, max, flags}]}"""
    global _by_char
    if _by_char is not None:
        return _by_char
    out: dict[str, dict] = {}
    for pr in pairs():
        for me, other in (("a", "b"), ("b", "a")):
            rec = out.setdefault(pr[me], {"jp": pr[me], "en": pr.get(me + "_en", ""),
                                          "partners": []})
            rec["partners"].append({
                "jp": pr[other],
                "en": pr.get(other + "_en", ""),
                "max": pr.get("max", ""),
                "flags": dict(pr.get("flags", {})),
            })
    for rec in out.values():
        rec["partners"].sort(key=lambda p: (p["en"] or p["jp"]).lower())
    _by_char = out
    return out


def chars() -> list[tuple[str, dict]]:
    return sorted(by_char().items(), key=lambda kv: (kv[1]["en"] or kv[1]["jp"]).lower())


def present_flags(payload: bytes) -> set[int]:
    """Every hash the save records as a set flag (``01 <u32 hash>`` entries)."""
    out: set[int] = set()
    for off in range(1, len(payload) - 4):
        if payload[off - 1] == 1:
            out.add(struct.unpack_from("<I", payload, off)[0])
    return out


def seen(partner: dict, present: set[int]) -> dict[str, bool]:
    return {r: h in present for r, h in partner.get("flags", {}).items()}


def rank_of(n_seen: int) -> str:
    return RANKS[max(0, n_seen - 1)] if n_seen else ""


# --------------------------------------------------------------------------
# the point table (issue #19's layout)
# --------------------------------------------------------------------------
def points_data() -> dict:
    global _points
    if _points is None:
        try:
            with open(POINTS_PATH, encoding="utf-8") as fh:
                _points = json.load(fh)
        except (OSError, ValueError):
            _points = {}
    return _points if _points is not None else {}


def max_points() -> int:
    return int(points_data().get("max_points") or MAX_POINTS)


def point_chars() -> list[tuple[str, str]]:
    """``(jp, en)`` for every character, in the game's canonical index order."""
    d = points_data()
    jp, en = d.get("chars_jp") or [], d.get("chars") or []
    return [(a, b or a) for a, b in zip(jp, en)]


def _known_hashes() -> set[int]:
    global _known
    if _known is None:
        _known = {h for _, _, h in (points_data().get("pairs") or [])}
    return _known


def point_pairs() -> list[tuple[int, str, str]]:
    """``(hash, jp_a, jp_b)`` for every pair the table covers."""
    jp = points_data().get("chars_jp") or []
    out = []
    for a, b, h in (points_data().get("pairs") or []):
        if a < len(jp) and b < len(jp):
            out.append((h, jp[a], jp[b]))
    return out


def point_partners() -> dict[str, list[dict]]:
    """jp -> ``[{jp, en, hash}]`` for every other character."""
    global _partners
    if _partners is not None:
        return _partners
    en = dict(point_chars())
    out: dict[str, list[dict]] = {}
    for h, a, b in point_pairs():
        out.setdefault(a, []).append({"jp": b, "en": en.get(b, b), "hash": h})
        out.setdefault(b, []).append({"jp": a, "en": en.get(a, a), "hash": h})
    for v in out.values():
        v.sort(key=lambda p: (p["en"] or p["jp"]).lower())
    _partners = out
    return out


def find_table(payload, start: int, end: int) -> dict | None:
    """Locate the support point table inside ``payload[start:end]``.

    Returns ``{pair hash: (points, extra, offset of the entry)}``, or ``None``
    when the block holds no table this build can recognise.  The table does not
    begin at a fixed offset — its alignment differs between saves — so the phase
    is derived from the entries themselves: every recognised pair hash sits at
    the same residue modulo 12.
    """
    known = _known_hashes()
    if not known or payload is None:
        return None
    start = max(0, int(start))
    stop = min(len(payload), int(end)) - (ENTRY_SIZE - 1)
    if stop <= start:
        return None
    unpack = struct.unpack_from
    hits: list[int] = []
    # the entries are not 4-byte aligned in the file, so scan byte by byte
    for off in range(start, stop):
        if unpack("<I", payload, off)[0] in known:
            hits.append(off)
    if len(hits) < 64:
        return None
    phases: dict[int, int] = {}
    for off in hits:
        r = (off - start) % ENTRY_SIZE
        phases[r] = phases.get(r, 0) + 1
    phase, count = max(phases.items(), key=lambda kv: kv[1])
    if count < 64:
        return None
    offs = [o for o in hits if (o - start) % ENTRY_SIZE == phase]
    out: dict[int, tuple[int, int, int]] = {}
    for off in range(offs[0], offs[-1] + 1, ENTRY_SIZE):
        h, pts, extra = unpack("<III", payload, off)
        if h in known:
            out[h] = (pts, extra, off)
    return out or None


def set_points(payload, offset: int, value: int) -> None:
    """Write the point value of the entry at ``offset`` (in place)."""
    struct.pack_into("<I", payload, offset + 4, max(0, min(int(value), 0xFFFFFFFF)))


def points_of(table: dict | None, pair_hash: int) -> int | None:
    if not table:
        return None
    row = table.get(pair_hash)
    return None if row is None else row[0]
