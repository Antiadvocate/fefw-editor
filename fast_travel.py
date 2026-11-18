"""Known Dagsion destination flags, independent of world-map/facility state.

Only value 1 and absence are writable. Never infer the list from its index or
create unscoped lookalike flags. See https://github.com/Destorino5/fefw-editor/blob/feature/part2-story/docs/fast-travel.md for evidence and limits.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import struct

import fefw_core as core

HERE = Path(__file__).resolve().parent
AVAILABLE = 1
MIN_ANCHORS = 3


class FastTravelError(core.SaveError):
    pass


@lru_cache(maxsize=1)
def catalog() -> dict[int, dict]:
    try:
        data = json.loads((HERE / "fast_travel_names.json").read_text(encoding="utf8"))
        if data["schema"] != 1:
            raise ValueError("unsupported catalogue version")
        entries = {int(h, 16): row for h, row in data["entries"].items()}
        for h, row in entries.items():
            if (not row["name"].startswith("拠点_FT_Hub_000_") or
                    "_ファストトラベル_" not in row["name"] or
                    core.id_hash(row["name"]) != h or not row["label"] or
                    row["area"] != "Dagsion" or type(row["locator_anchor"]) is not bool or
                    row["coverage"] not in ("Confirmed list", "Travel tested", "Effect unknown")):
                raise ValueError("invalid destination identity")
        if len(entries) < MIN_ANCHORS:
            raise ValueError("too few catalogue entries")
        return entries
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise FastTravelError(f"Cannot load fast_travel_names.json: {exc}") from exc


def apply_labels(names: dict[int, dict]) -> None:
    """Use screenshot-confirmed English names; keep exact keys in Reads as."""
    entries = catalog()
    for h, row in entries.items():
        if names.get(h, {}).get("name", row["name"]) != row["name"]:
            raise FastTravelError(f"Conflicting flag name for {h:08x}")
    for h, row in entries.items():
        names[h] = {**names.get(h, {}), "name": row["name"],
                    "label": f"Fast travel: {row['label']}",
                    "kind": "fast_travel"}


def identifying_hashes() -> set[int]:
    """Only the original 16 destinations are accepted locator anchors."""
    return {h for h, row in catalog().items() if row["locator_anchor"]}


def locate(f: core.SaveFile) -> core.FlagMap:
    """Require one structurally valid map with at least three known identities."""
    blocks = [b for b in f.blocks if b.name == "GameUserData"]
    if len(blocks) != 1:
        raise FastTravelError("No unique GameUserData block; editing is disabled.")
    hashes = catalog().keys()
    candidates = [m for m in core.flag_maps(f)
                  if any(fl.hash in hashes for fl in m.flags)]
    if len(candidates) != 1:
        raise FastTravelError("No unique fast-travel list found; this save is read-only here.")
    fm = candidates[0]
    if len({fl.hash for fl in fm.flags} & identifying_hashes()) < MIN_ANCHORS:
        raise FastTravelError("At least three original destinations must be present to identify this list.")
    if len({fl.hash for fl in fm.flags}) != len(fm.flags):
        raise FastTravelError("Duplicate fast-travel-list keys; editing is disabled.")
    tree = f.tree()
    node = tree.node_at(fm.start)
    user = tree.node_at(blocks[0].start)
    group = tree.nodes[node].parent if node >= 0 else -1
    if (node < 0 or user < 0 or group < 0 or tree.nodes[node].struct or
            not tree.nodes[group].struct or tree.nodes[group].parent != user or
            any(n.parent == node for n in tree.nodes)):
        raise FastTravelError("Unrecognised fast-travel-list structure; editing is disabled.")
    return fm


def read(f: core.SaveFile) -> dict[int, int]:
    return {fl.hash: fl.value for fl in locate(f).flags}


def state_label(value: int | None) -> str:
    if value is None:
        return "Absent"
    if value == AVAILABLE:
        return "Available (1)"
    return f"Unknown ({value}); preserved"


def edited(f: core.SaveFile, edits: dict[int, int | None]) -> bytearray:
    """Atomic allowlisted add/remove, preserving other records' exact encoding."""
    cat = catalog()
    for h, value in edits.items():
        if h not in cat or (value is not None and
                            (type(value) is not int or value != AVAILABLE)):
            raise FastTravelError("Only known destinations and availability/removal are supported.")
    fm = locate(f)
    present = {fl.hash: fl.value for fl in fm.flags}
    for h in edits:
        if h in present and present[h] != AVAILABLE:
            raise FastTravelError(f"{cat[h]['label']} has unknown state {present[h]}; unchanged.")
    effective = {h: v for h, v in edits.items() if present.get(h) != v}
    if not effective:
        return bytearray(f.payload)
    remaining = (present.keys() - effective.keys()) | {h for h, v in effective.items() if v is not None}
    if len(remaining & identifying_hashes()) < MIN_ANCHORS:
        raise FastTravelError("Keep at least three original destinations so the list remains identifiable.")
    records = []
    for fl in fm.flags:
        if fl.hash in effective and effective[fl.hash] is None:
            continue
        start = fl.offset - (5 if fl.wide else 4)
        records.append(bytes(f.payload[start:fl.offset + (4 if fl.wide else 1)]))
    for h, v in effective.items():
        if h not in present and v is not None:
            records.append(struct.pack("<IB", h, v))
    if len(records) > 65535:
        raise FastTravelError("The fast-travel list is full.")
    body = bytes([f.payload[fm.start + 4]]) + struct.pack("<H", len(records)) + b"".join(records)
    return core.replace_content(f, fm.start, body)
