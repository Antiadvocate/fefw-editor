"""Read-only Boon reference data and the observed EXP-associated record.

No save writes: purchase and activation storage require controlled game tests.
The candidate hash is an observation, not a decoded Boon identity.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

import audiences
import fefw_core as core

HERE = Path(__file__).resolve().parent
EXP_CANDIDATE = 0x3b6429de


class BoonError(core.SaveError):
    pass


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    try:
        data = json.loads((HERE / "boon_catalog.json").read_text(encoding="utf8"))
        if data["schema"] != 1:
            raise ValueError("unsupported catalogue version")
        groups = data["groups"]
        seen = set()
        for group in groups:
            if not group["name"] or not group["label"] or group["name"] in seen:
                raise ValueError("missing or repeated Boon group")
            seen.add(group["name"])
            for field in ("effect_code", "operation_code"):
                if type(group[field]) is not int or not 1 <= group[field] <= 255:
                    raise ValueError("invalid reference effect")
            if not group["tiers"]:
                raise ValueError("missing reference tiers")
            for index, tier in enumerate(group["tiers"], 1):
                if type(tier["tier"]) is not int or tier["tier"] != index:
                    raise ValueError("invalid tier order")
                for field, maximum in (("value", 255), ("clear_count", 255), ("cost", 65535)):
                    if type(tier[field]) is not int or not 0 <= tier[field] <= maximum:
                        raise ValueError("invalid reference value")
        if not groups:
            raise ValueError("empty catalogue")
        return groups
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BoonError(f"Cannot load boon_catalog.json: {exc}") from exc


def read_observation(f: core.SaveFile) -> dict:
    """Return raw evidence only, never infer ownership or activation."""
    try:
        values = audiences.read(f)
    except core.SaveError as exc:
        raise BoonError("Shared map cannot be identified uniquely; Boon observation unavailable.") from exc
    user = core.user_data(f)
    if user < 0:
        raise BoonError("Player resource header is not recognised; observation unavailable.")
    return {"karma_shards": f.u32(user + core.KARMA_AT),
            "exp_candidate": values.get(EXP_CANDIDATE)}


def observation_label(value: int | None) -> str:
    stored = "Not stored" if value is None else f"Stored value {value}"
    return f"{stored}; purchase and activation meaning unconfirmed"


def matching_rows(query: str = "") -> list[tuple[str, dict, dict]]:
    query = query.strip().casefold()
    return [(f"{i}:{tier['tier']}", group, tier)
            for i, group in enumerate(catalog()) for tier in group["tiers"]
            if not query or query in f"{group['label']} {group['name']}".casefold()]
