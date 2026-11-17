"""Allowlisted switches in GameUserData's general, history and progression maps.

Service switches, temple-transfer registrations and ordinary travel flags are
independent. Do not identify this map by its enumerated index.
"""
from functools import lru_cache
import json
from pathlib import Path
import struct

import fefw_core as core

HERE = Path(__file__).resolve().parent
# These progression identities are never edited by this module.
# Journal sections are editable and must not identify the map after removal.
ANCHORS = frozenset(core.id_hash(key) for key in (
    '拠点_進行_初回自由行動',
    '拠点_進行_ファストトラベルエリア解放許可', '拠点_進行_拠点地図表示許可'))
MIN_ANCHORS = 2
SEWERS = 0x7d18367a
SEWERS_DIALOGUE = 'MID_LGV_1KAI_c02_LG11_003_m06'
HISTORY_MEMBER = 0xb631f2c1
UNAVAILABLE = 'unavailable'
GENERAL_MEMBER = 0x972fa7ee
PROGRESSION_MEMBER = 0x4ad575a2
MOVEMENT = {core.id_hash(key): key for key in (
    '行動範囲制限_上層', '行動範囲制限_中層', '行動範囲制限_下層',
    '行動範囲制限_富裕区-商業区')}
# The native Cai Chapter 1 checkpoint predates all general-map anchors. Its
# complete 13-member flag-group layout is an independently captured identity.
FLAG_GROUP_MEMBERS = frozenset((0x25207c4c, 0x58a0be00, GENERAL_MEMBER,
    HISTORY_MEMBER, 0x06c136c7, 0xf56d6832, 0x2bed8663, 0x64aba34f,
    0xe9bc5b65, 0xe5834a3c, 0x4ad575a2, 0x0802e120, 0x8186b481))


class FacilityError(core.SaveError):
    pass


@lru_cache(maxsize=1)
def catalog():
    try:
        data = json.loads((HERE / 'facility_names.json').read_text(encoding='utf8'))
        if data['schema'] != 1 or not data['entries']:
            raise ValueError('unsupported or empty catalogue')
        cat = {int(h, 16): row for h, row in data['entries'].items()}
        for h, row in cat.items():
            expected = '禁止_' if row['polarity'] == 'restriction' else (
                '神殿_転移_' if row['kind'] == 'Gate registration' else '機能開放_')
            identity_ok = (row['name'] == MOVEMENT[h] and row.get('store') == 'progression'
                           and row['kind'] == 'Area access' and row['polarity'] == 'restriction'
                           if h in MOVEMENT else
                           row.get('store', 'general') == 'general' and
                           (row['name'] == SEWERS_DIALOGUE if h == SEWERS
                            else row['name'].startswith(expected)))
            if (core.id_hash(row['name']) != h or not identity_ok
                    or row['kind'] not in ('Service', 'Gate registration', 'Journal', 'Area access')
                    or row['polarity'] not in ('unlock', 'restriction')
                    or row['coverage'] not in ('Inferred', 'Unlock tested', 'Registration tested', 'Game-tested', 'Conditional pass')
                    or not row['label'] or not row['note'] or h in ANCHORS):
                raise ValueError('invalid facility identity')
        return cat
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise FacilityError(f'Cannot load facility_names.json: {exc}') from exc


def apply_labels(names):
    updates = {}
    for h, row in catalog().items():
        key = row['name']
        if names.get(h, {}).get('name', key) != key:
            raise FacilityError(f'Conflicting facility identity for {h:08x}')
        prefix = ('Movement restricted: ' if h in MOVEMENT else
                  'Disabled: ' if row['polarity'] == 'restriction' else
                  'Registered: ' if row['kind'] == 'Gate registration' else
                  'Function unlocked: ' if row['kind'] in ('Journal', 'Area access') else 'Facility unlocked: ')
        updates[h] = {**names.get(h, {}), 'name': key, 'label': prefix + row['label'], 'kind': 'facility'}
    names.update(updates)


def locate(f):
    users = [b for b in f.blocks if b.name == 'GameUserData']
    identities = ANCHORS | (catalog().keys() - {SEWERS} - MOVEMENT.keys())
    candidates = [m for m in core.flag_maps(f) if any(v.hash in identities for v in m.flags)]
    if len(users) != 1 or len(candidates) != 1:
        raise FacilityError('No unique general facility map; these controls are read-only.')
    fm = candidates[0]
    hashes = {v.hash for v in fm.flags}
    if len(hashes & ANCHORS) < MIN_ANCHORS or len(hashes) != len(fm.flags):
        raise FacilityError('Facility map needs two unchanged anchors and no duplicate keys.')
    tree = f.tree()
    node, user = tree.node_at(fm.start), tree.node_at(users[0].start)
    group = tree.nodes[node].parent if node >= 0 else -1
    if (node < 0 or user < 0 or group < 0 or tree.nodes[node].struct
            or not tree.nodes[group].struct or tree.nodes[group].parent != user
            or any(n.parent == node for n in tree.nodes)):
        raise FacilityError('Unrecognised facility map structure; editing is disabled.')
    return fm


def flag_group(f):
    """Anchored group, or the complete native early-checkpoint layout.

    This fallback identifies sibling stores only. It does not relax the
    general function map's two-anchor guard.
    """
    try:
        general = locate(f)
    except FacilityError:
        general = None
    tree = f.tree()
    if general is not None:
        return tree, tree.nodes[tree.node_at(general.start)].parent, general.start
    users = [b for b in f.blocks if b.name == 'GameUserData']
    if len(users) != 1 or f.payload[users[0].start+4] != 23:
        raise FacilityError('Unrecognised early flag group; editing is disabled.')
    user = tree.node_at(users[0].start); hits = []
    for index, node in enumerate(tree.nodes):
        if node.parent != user or not node.struct: continue
        count = f.u32(node.start) >> 24; table = f.ptr(node.start)
        if count != len(FLAG_GROUP_MEMBERS) or table+8*count != node.end: continue
        rows = [(f.u32(table+8*i), f.ptr(table+8*i+4)) for i in range(count)]
        if ({k for k,v in rows} != FLAG_GROUP_MEMBERS
                or len({v for k,v in rows}) != count
                or {v for k,v in rows} != {n.start for n in tree.nodes if n.parent == index}): continue
        general_start = dict(rows)[GENERAL_MEMBER]
        general_node = tree.nodes[tree.node_at(general_start)]
        maps = [m for m in core.flag_maps(f) if m.start == general_start]
        if general_node.struct or len(maps) != 1: continue
        keys = [v.hash for v in maps[0].flags]
        # This is specifically the pre-free-time profile. Do not let the
        # fallback bypass duplicate/sparse/ambiguous anchored-map refusals.
        if len(set(keys)) != len(keys) or set(keys) & ANCHORS: continue
        hits.append((index, general_start))
    if len(hits) != 1:
        raise FacilityError('No unique supported flag group; editing is disabled.')
    return tree, hits[0][0], hits[0][1]


def locate_member(f, member):
    """Find a flag-group member by structural identity, including an empty map."""
    tree, group, general_start = flag_group(f)
    parent = tree.nodes[group]
    table = f.ptr(parent.start)
    count = f.u32(parent.start) >> 24
    rows = [(f.u32(table+8*i), f.ptr(table+8*i+4)) for i in range(count)]
    if (table+8*count != parent.end or len({k for k, v in rows}) != count
            or len({v for k, v in rows}) != count
            or {v for k, v in rows} != {n.start for n in tree.nodes if n.parent == group}):
        raise FacilityError('Unrecognised function flag group; no changes made.')
    targets = [v for k, v in rows if k == member]
    if len(targets) != 1:
        raise FacilityError('No unique requested flag member; no changes made.')
    at = targets[0]; index = tree.node_at(at); node = tree.nodes[index]
    if node.struct or node.parent != group or any(n.parent == index for n in tree.nodes):
        raise FacilityError('Unexpected flag member structure; no changes made.')
    maps = [m for m in core.flag_maps(f) if m.start == at]
    if not maps and bytes(f.payload[at+4:node.end]) == bytes(4):
        return core.FlagMap(-1, at, [])  # Empty kind-0 list plus alignment.
    if (len(maps) != 1 or len({v.hash for v in maps[0].flags}) != len(maps[0].flags)
            or f.ptr(at) != node.end):
        raise FacilityError('Invalid flag member records; no changes made.')
    return maps[0]


def locate_history(f):
    return locate_member(f, HISTORY_MEMBER)


def member_for(h):
    return PROGRESSION_MEMBER if h in MOVEMENT else HISTORY_MEMBER if h == SEWERS else GENERAL_MEMBER


def read(f):
    values = {v.hash: v.value for v in locate(f).flags}
    # A same-hash record in another map must never stand in for dialogue history.
    values.pop(SEWERS, None)
    try:
        history = locate_history(f)
    except FacilityError:
        values[SEWERS] = UNAVAILABLE
    else:
        values.update({v.hash: v.value for v in history.flags if v.hash == SEWERS})
    for h in MOVEMENT: values.pop(h, None)
    try:
        progression = locate_member(f, PROGRESSION_MEMBER)
    except FacilityError:
        values.update({h: UNAVAILABLE for h in MOVEMENT})
    else:
        values.update({v.hash: f'wide {v.value}' if v.wide else v.value
                       for v in progression.flags if v.hash in MOVEMENT})
    return values


def enabled(h, value):
    """Logical switch only, not a prediction that the facility is usable."""
    if value not in (None, 0, 1):
        return None
    active = value == 1
    return not active if catalog()[h]['polarity'] == 'restriction' else active


def state_label(h, value):
    if value == UNAVAILABLE:
        return 'Unavailable; read-only'
    state = enabled(h, value)
    if state is None:
        return f'Unknown ({value}); preserved'
    return 'Enabled' if state else 'Disabled'


def edited(f, edits):
    """Apply a logical enable/disable batch atomically; retain other encodings."""
    cat = catalog()
    for h, state in edits.items():
        if type(h) is not int or h not in cat or type(state) is not bool:
            raise FacilityError('Choose known facility switches and an enable/disable action.')
    needed = {member_for(h) for h in edits} if edits else {GENERAL_MEMBER}
    maps = {member: locate(f) if member == GENERAL_MEMBER else locate_member(f, member)
            for member in needed}
    plans = {}
    for h, state in edits.items():
        fm = maps[member_for(h)]
        if h in MOVEMENT and any(v.hash == h and v.wide for v in fm.flags):
            raise FacilityError(f'{cat[h]["label"]} has an unknown wide encoding; batch unchanged.')
        present = {v.hash: v.value for v in fm.flags}
        old = enabled(h, present.get(h))
        if old is None:
            raise FacilityError(f'{cat[h]["label"]} has an unknown saved value; batch unchanged.')
        if old != state:
            active = not state if cat[h]['polarity'] == 'restriction' else state
            plans.setdefault(fm.start, (fm, {}))[1][h] = 1 if active else None
    # Validate the whole batch before rebuilding either map. Descending offsets
    # keep the other map's addresses stable as the containing object is resized.
    result = core.SaveFile(f.payload)
    for at in sorted(plans, reverse=True):
        fm, effective = plans[at]
        result = core.SaveFile(_edit_map(result, fm, effective))
    return bytearray(result.payload)


def _edit_map(f, fm, effective):
    present = {v.hash: v.value for v in fm.flags}
    records = []
    for fl in fm.flags:
        if fl.hash in effective:
            if effective[fl.hash] is not None:
                records.append(struct.pack('<IB', fl.hash, 1))
        else:
            start = fl.offset - (5 if fl.wide else 4)
            records.append(bytes(f.payload[start:fl.offset + (4 if fl.wide else 1)]))
    for h, value in effective.items():
        if h not in present and value is not None:
            records.append(struct.pack('<IB', h, 1))
    if len(records) > 65535:
        raise FacilityError('The selected flag map is full.')
    body = bytes([f.payload[fm.start + 4]]) + struct.pack('<H', len(records)) + b''.join(records)
    return core.replace_content(f, fm.start, body)
