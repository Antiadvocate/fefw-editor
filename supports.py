"""
Support chart data for Fire Emblem: Fortune's Weave.

Two separate things live here:

* **The pair chart** — every support pair the game data defines, with the
  highest rank each pair can reach (C / B / A / S).  This comes from
  ``GameData/Reliance.bin`` and the ``支援会話_<A>_<B>_<rank>`` flag names, and
  is baked into ``supports.json`` so the editor needs no ROM access.

* **Conversation flags** — the save records ``支援会話_<A>_<B>_<rank>`` as an
  ordinary flag once that conversation has been seen, so the editor can show
  which of a pair's conversations this save has registered.

Support *level* and *points* are not exposed by the save format yet (see
README), so nothing here pretends to know them.
"""

from __future__ import annotations

import json
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "supports.json")
RANKS = ("C", "B", "A", "S")

_pairs: list[dict] | None = None
_by_char: dict[str, dict] | None = None


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
