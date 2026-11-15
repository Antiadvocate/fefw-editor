"""Identified tutorial flags, conservative reads, and atomic list edits.

Only availability (2) and removal are writable here. Other stored states are
reported verbatim. See docs/tutorials.md for the evidence and limitations.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import struct

import fefw_core as core

HERE = Path(__file__).resolve().parent
AVAILABLE = 2


class TutorialError(core.SaveError):
    pass


@lru_cache(maxsize=1)
def catalog() -> dict[int, dict]:
    try:
        data = json.loads((HERE / "tutorial_names.json").read_text(encoding="utf8"))
        if data["schema"] != 1:
            raise ValueError("unsupported catalogue version")
        entries = {int(h, 16): row for h, row in data["entries"].items()}
        for h, row in entries.items():
            if (not row["name"].startswith("TUTO_") or
                    core.id_hash(row["name"]) != h or not row["label"]):
                raise ValueError("invalid tutorial identity")
        if not entries:
            raise ValueError("empty catalogue")
        return entries
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise TutorialError(f"Cannot load tutorial_names.json: {exc}") from exc


def apply_labels(names: dict[int, dict]) -> None:
    """Overlay verified labels without translating or changing hashed keys."""
    for h, row in catalog().items():
        previous = names.get(h, {})
        if previous.get("name", row["name"]) != row["name"]:
            raise TutorialError(f"Conflicting flag name for {h:08x}")
        names[h] = {**previous, "name": row["name"],
                    "label": "Tutorial: " + row["label"], "kind": "tutorial"}


@lru_cache(maxsize=1)
def _tutorial_hashes() -> frozenset[int]:
    # The wider name dictionary helps detect split/ambiguous lists even when
    # an entry does not yet have a verified English label in our catalogue.
    hashes = set(catalog())
    try:
        raw = json.loads((HERE / "flag_names.json").read_text(encoding="utf8"))
        hashes.update(int(h, 16) for h, row in raw.items()
                      if row.get("name", "").startswith("TUTO_")
                      and core.id_hash(row["name"]) == int(h, 16))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise TutorialError(f"Cannot load flag_names.json: {exc}") from exc
    return frozenset(hashes)


def locate(f: core.SaveFile) -> core.FlagMap:
    """Find a unique populated tutorial map, never guess a numbered list."""
    hashes = _tutorial_hashes()
    candidates = [m for m in core.flag_maps(f)
                  if any(fl.hash in hashes for fl in m.flags)]
    if len(candidates) != 1:
        raise TutorialError("No unique tutorial list found; this save is read-only here.")
    fm = candidates[0]
    known = {fl.hash for fl in fm.flags if fl.hash in hashes}
    if core.id_hash("TUTO_オートセーブ") not in known and len(known) < 3:
        raise TutorialError("Too little evidence to identify the tutorial list safely.")
    if len({fl.hash for fl in fm.flags}) != len(fm.flags):
        raise TutorialError("Duplicate tutorial-list keys; editing is disabled.")
    tree = core.SaveTree(f.payload)
    node = tree.node_at(fm.start)
    if node < 0 or any(n.parent == node for n in tree.nodes):
        raise TutorialError("Unrecognised tutorial-list structure; editing is disabled.")
    return fm


def read(f: core.SaveFile) -> dict[int, int]:
    """Present values including unnamed entries; absence is not zero."""
    return {fl.hash: fl.value for fl in locate(f).flags}


def state_label(value: int | None) -> str:
    if value is None:
        return "Absent"
    if value == AVAILABLE:
        return "Available (2)"
    if value == 1:
        return "Present (1)"
    return f"Unknown ({value}); preserved"


def edited(f: core.SaveFile, edits: dict[int, int | None]) -> bytearray:
    """Return a new payload, preserving every unselected record's raw bytes.

    Validate the entire operation before building anything. Unknown states
    cannot be overwritten by this guided page; the advanced Flags page remains
    separate. None removes a record; it does not write a zero-valued record.
    """
    cat = catalog()
    for h, value in edits.items():
        if h not in cat or (value is not None and (type(value) is not int or value != AVAILABLE)):
            raise TutorialError("Only identified tutorials and availability/removal are supported.")
    fm = locate(f)
    present = {fl.hash: fl.value for fl in fm.flags}
    for h in edits:
        if h in present and present[h] not in (1, AVAILABLE):
            raise TutorialError(f"{cat[h]['label']} has unknown state {present[h]}; unchanged.")
    effective = {h: v for h, v in edits.items() if present.get(h) != v}
    if not effective:
        return bytearray(f.payload)
    records = []
    for fl in fm.flags:
        if fl.hash in effective and effective[fl.hash] is None:
            continue
        start = fl.offset - (5 if fl.wide else 4)
        raw = bytearray(f.payload[start:fl.offset + (4 if fl.wide else 1)])
        if fl.hash in effective:
            raw[-(4 if fl.wide else 1):] = core.flag_bytes(fl, effective[fl.hash])
        records.append(bytes(raw))
    for h, v in effective.items():
        if h not in present and v is not None:
            records.append(struct.pack("<IB", h, v))
    if len(records) > 65535:
        raise TutorialError("The tutorial list is full.")
    # Removing its last identifying entries would make subsequent additions
    # ambiguous. Refuse rather than create a list the editor cannot locate.
    remaining = (present.keys() - effective.keys()) | {h for h, v in effective.items() if v is not None}
    known = remaining & _tutorial_hashes()
    if core.id_hash("TUTO_オートセーブ") not in known and len(known) < 3:
        raise TutorialError("Keep Autosave or at least three identified tutorials so the list remains identifiable.")
    body = bytes([f.payload[fm.start + 4]]) + struct.pack("<H", len(records)) + b"".join(records)
    return core.replace_content(f, fm.start, body)
