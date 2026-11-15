"""Reference data and isolated disable markers for two existing first-tier Boons.

Only the observed ownership=1, disable=absent/1 state is editable. Purchase,
higher tiers and other Boon activation keys are not inferred from these hashes.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

import audiences
import fefw_core as core

HERE = Path(__file__).resolve().parent
EXP_CANDIDATE = 0x3b6429de
EXP_DISABLED = 0x6447f467
WEAPONS_PURCHASE = 0x5bfcaa34
WEAPONS_DISABLED = 0xddb8d06b


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
    """Read the observed records; unknown/absent values remain distinct."""
    try:
        values = audiences.read(f)
    except core.SaveError as exc:
        raise BoonError("Shared map cannot be identified uniquely; Boon observation unavailable.") from exc
    user = core.user_data(f)
    if user < 0:
        raise BoonError("Player resource header is not recognised; observation unavailable.")
    return {"karma_shards": f.u32(user + core.KARMA_AT),
            "exp_candidate": values.get(EXP_CANDIDATE),
            "exp_disabled": values.get(EXP_DISABLED),
            "weapons_purchase": values.get(WEAPONS_PURCHASE),
            "weapons_disabled": values.get(WEAPONS_DISABLED)}


def observation_label(value: int | None) -> str:
    stored = "Not stored" if value is None else f"Stored value {value}"
    return f"{stored}; other tiers and purchase editing unconfirmed"


def exp_edit_reason(observation: dict) -> str:
    """An empty reason permits only the already-observed first-tier toggle."""
    if observation['exp_candidate'] != 1:
        return "Requires the observed, already-owned EXP +10% state (stored record 1)."
    if observation['exp_disabled'] not in (None, 1):
        return f"Unknown EXP disable value ({observation['exp_disabled']}); preserved."
    return ""


def exp_state_label(observation: dict) -> str:
    if exp_edit_reason(observation):
        return "Unknown / read-only"
    return "Off" if observation['exp_disabled'] == 1 else "On"


def edited_exp_active(f: core.SaveFile, active: bool) -> bytearray:
    """Add/remove only the EXP disable record; never buy, refund or change tiers."""
    if type(active) is not bool:
        raise BoonError("Choose On or Off for the existing EXP +10% Boon.")
    observation = read_observation(f)
    reason = exp_edit_reason(observation)
    if reason:
        raise BoonError(reason)
    disabled = observation['exp_disabled']
    if (active and disabled is None) or (not active and disabled == 1):
        return bytearray(f.payload)
    fm = audiences.locate(f)
    if active:
        flag = next(fl for fl in fm.flags if fl.hash == EXP_DISABLED)
        return core.flag_remove(f, fm, flag)
    return core.flag_add(f, fm, EXP_DISABLED, 1)


def weapons_edit_reason(observation: dict) -> str:
    if observation['weapons_purchase'] != 1:
        return "Requires the observed, already-purchased Weapons Discount 10% Boon."
    if observation['weapons_disabled'] not in (None, 1):
        return f"Unknown Weapons Discount disable value ({observation['weapons_disabled']}); preserved."
    return ""


def weapons_state_label(observation: dict) -> str:
    if weapons_edit_reason(observation):
        return "Unknown / read-only"
    return "Off" if observation['weapons_disabled'] == 1 else "On"


def edited_weapons_active(f: core.SaveFile, active: bool) -> bytearray:
    """Toggle the captured purchased 10% state; do not buy or change any tier."""
    if type(active) is not bool:
        raise BoonError("Choose On or Off for the existing Weapons Discount 10% Boon.")
    observation = read_observation(f)
    reason = weapons_edit_reason(observation)
    if reason:
        raise BoonError(reason)
    disabled = observation['weapons_disabled']
    if (active and disabled is None) or (not active and disabled == 1):
        return bytearray(f.payload)
    fm = audiences.locate(f)
    if active:
        flag = next(fl for fl in fm.flags if fl.hash == WEAPONS_DISABLED)
        return core.flag_remove(f, fm, flag)
    return core.flag_add(f, fm, WEAPONS_DISABLED, 1)


def matching_rows(query: str = "") -> list[tuple[str, dict, dict]]:
    query = query.strip().casefold()
    return [(f"{i}:{tier['tier']}", group, tier)
            for i, group in enumerate(catalog()) for tier in group["tiers"]
            if not query or query in f"{group['label']} {group['name']} {group.get('game_label', '')}".casefold()]


def display_name(group: dict) -> str:
    return group.get('game_label') or group['label']
