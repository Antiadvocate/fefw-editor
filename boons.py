"""Catalogue-scoped Boon levels and independent On/Off markers.

EXP tier 1 and Weapons Discount tiers 1/2 have game evidence. Brawling and
Black-Magic tier 1 have isolated save captures. Remaining keys and tiers
extrapolate the common hash pattern; see https://github.com/Destorino5/fefw-editor/blob/feature/part2-story/docs/boons.md. The original
first-tier helpers remain available for reproducing the earlier experiments.
"""
from __future__ import annotations

from functools import lru_cache
import json
import struct
from pathlib import Path

import audiences
import fefw_core as core

HERE = Path(__file__).resolve().parent
EXP_CANDIDATE = 0x3b6429de
EXP_DISABLED = 0x6447f467
WEAPONS_PURCHASE = 0x5bfcaa34
WEAPONS_DISABLED = 0xddb8d06b
LEVEL_PREFIX = '因果報酬_レベル_'
# Low 32-bit FNV-1 state before the UTF-8 group name. Independently reproduces
# both captured disable keys; the original prefix text is not yet recovered.
DISABLED_PREFIX_STATE = 0xa21ab2b4
GAME_TESTED_TIERS = {('経験値', 1), ('武器割引', 1), ('武器割引', 2)}
SAVE_CAPTURED_TIERS = {('技能経験格闘', 1), ('技能経験黒魔法', 1)}
# Save keys use abbreviated skill names, not the Reward.bin display groups.
# Brawling and Black-Magic are independently captured; the other six aliases
# are inferred from that pattern and still require game acceptance. This is
# deliberately NOT a general string/UTF-8 truncation rule.
SKILL_KEY_NAMES = {
    '技能経験格闘': '技能経験格',
    '技能経験黒魔法': '技能経験黒',
    '技能経験白魔法': '技能経験白',
    '技能経験歩兵': '技能経験歩',
    '技能経験騎兵': '技能経験騎',
    '技能経験重装': '技能経験重',
    '技能経験飛行': '技能経験飛',
    '技能経験指揮': '技能経験指',
}


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


def group_keys(name: str) -> tuple[int, int]:
    if name not in {g['name'] for g in catalog()}:
        raise BoonError('Choose a Boon from the catalogue.')
    name = SKILL_KEY_NAMES.get(name, name)
    disabled = DISABLED_PREFIX_STATE
    for byte in name.encode('utf8'):
        disabled = ((disabled * 0x1b3) & 0xffffffff) ^ byte
    return core.id_hash(LEVEL_PREFIX + name), disabled


def evidence_label(name: str, tier: int) -> str:
    if (name, tier) in GAME_TESTED_TIERS:
        return 'Game-tested'
    if (name, tier) in SAVE_CAPTURED_TIERS:
        return 'Save-verified'
    return 'Inferred'


def apply_labels(names: dict[int, dict]) -> None:
    """Name all known tier/disable records without inventing the Off prefix."""
    updates = {}
    for group in catalog():
        name = group['name']
        level, disabled = group_keys(name)
        key = LEVEL_PREFIX + SKILL_KEY_NAMES.get(name, name)
        if names.get(level, {}).get('name', key) != key:
            raise BoonError(f'Conflicting Boon level identity for {level:08x}')
        # The original disable prefix text is unrecovered. Keep a known
        # original if supplied later; otherwise Reads As is empty, not guessed.
        off_key = names.get(disabled, {}).get('name', '')
        if off_key and core.id_hash(off_key) != disabled:
            raise BoonError(f'Conflicting Boon disable identity for {disabled:08x}')
        for h, original, label in (
                (level, key, 'Boon tier: ' + display_name(group)),
                (disabled, off_key, 'Boon disabled: ' + display_name(group))):
            if h in updates:
                raise BoonError('Ambiguous Boon label identities.')
            updates[h] = {**names.get(h, {}), 'name': original, 'label': label, 'kind': 'boon'}
    names.update(updates)


def read_state(f: core.SaveFile) -> dict:
    observation = read_observation(f)  # Validates the shared map and resource header.
    values = audiences.read(f)
    groups = {}
    seen = set()
    for group in catalog():
        name = group['name']
        level, disabled = group_keys(name)
        if level == disabled or level in seen or disabled in seen:
            raise BoonError('Ambiguous Boon key mapping; editing is disabled.')
        seen.update((level, disabled))
        groups[name] = {'level': values.get(level), 'disabled': values.get(disabled)}
    return {'karma_shards': observation['karma_shards'], 'groups': groups}


def group_edit_reason(group: dict, state: dict) -> str:
    level, disabled = state['level'], state['disabled']
    if level is not None and (type(level) is not int or not 0 <= level <= len(group['tiers'])):
        return f'Unknown stored tier ({level}); preserved.'
    if disabled is not None and (type(disabled) is not int or disabled != 1):
        return f'Unknown On/Off value ({disabled}); preserved.'
    return ''


def row_state(group: dict, tier: dict, state: dict) -> str:
    if group_edit_reason(group, state):
        return 'Unknown / read-only'
    level = state['level'] or 0
    if tier['tier'] > level:
        return 'Not owned'
    if tier['tier'] < level:
        return f'Below tier {level}'
    return 'Off' if state['disabled'] == 1 else 'On'


def edited_groups(f: core.SaveFile, *, levels: dict | None = None,
                  active: dict | None = None) -> bytearray:
    """Atomically edit allowlisted levels/switches; never charge Karma or set clears.

    Level 0 removes ownership. Tier changes preserve activation; active requests
    require ownership after the requested level changes. Unknown states fail
    before writing, including in a bulk request. Untouched record encodings and
    noncanonical-but-known zero/wide no-op states remain byte-identical.
    """
    levels = {} if levels is None else levels
    active = {} if active is None else active
    if not isinstance(levels, dict) or not isinstance(active, dict):
        raise BoonError('Boon edits must identify catalogue groups.')
    groups = {g['name']: g for g in catalog()}
    for name, value in levels.items():
        if name not in groups or type(value) is not int or not 0 <= value <= len(groups[name]['tiers']):
            raise BoonError('Choose a listed tier, or remove ownership.')
    for name, value in active.items():
        if name not in groups or type(value) is not bool:
            raise BoonError('Choose On or Off for a catalogue Boon.')
    observed = read_state(f)['groups']
    requested = {}
    for name in levels.keys() | active.keys():
        state = observed[name]
        reason = group_edit_reason(groups[name], state)
        if reason:
            raise BoonError(f'{display_name(groups[name])}: {reason}')
        level_hash, disabled_hash = group_keys(name)
        level = levels.get(name, state['level'] or 0)
        if name in levels and level != (state['level'] or 0):
            requested[level_hash] = level or None
        if name in active:
            if level == 0:
                raise BoonError('Set an owned tier before switching a Boon On or Off.')
            requested[disabled_hash] = None if active[name] else 1
    fm = audiences.locate(f)
    present = {fl.hash: fl.value for fl in fm.flags}
    effective = {h: v for h, v in requested.items() if present.get(h) != v}
    if not effective:
        return bytearray(f.payload)
    records = []
    for fl in fm.flags:
        if fl.hash in effective and effective[fl.hash] is None:
            continue
        start = fl.offset - (5 if fl.wide else 4)
        raw = bytes(f.payload[start:fl.offset + (4 if fl.wide else 1)])
        if fl.hash in effective:
            value = effective[fl.hash]
            raw = (struct.pack('<IBi', fl.hash, 255, value) if fl.wide
                   else struct.pack('<IB', fl.hash, value))
        records.append(raw)
    # Stable catalogue/hash order makes output independent of request ordering.
    for h in sorted(effective):
        if h not in present and effective[h] is not None:
            records.append(struct.pack('<IB', h, effective[h]))
    if len(records) > 65535:
        raise BoonError('The shared flag map is full.')
    body = bytes([f.payload[fm.start + 4]]) + struct.pack('<H', len(records)) + b''.join(records)
    return core.replace_content(f, fm.start, body)


def max_levels() -> dict[str, int]:
    return {g['name']: len(g['tiers']) for g in catalog()}
