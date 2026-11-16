"""Allowlisted function and facility switches in the general GameUserData flag map.

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
            if (core.id_hash(row['name']) != h or not row['name'].startswith(expected)
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
        prefix = ('Disabled: ' if row['polarity'] == 'restriction' else
                  'Registered: ' if row['kind'] == 'Gate registration' else
                  'Function unlocked: ' if row['kind'] in ('Journal', 'Area access') else 'Facility unlocked: ')
        updates[h] = {**names.get(h, {}), 'name': key, 'label': prefix + row['label'], 'kind': 'facility'}
    names.update(updates)


def locate(f):
    users = [b for b in f.blocks if b.name == 'GameUserData']
    identities = ANCHORS | catalog().keys()
    candidates = [m for m in core.flag_maps(f) if any(v.hash in identities for v in m.flags)]
    if len(users) != 1 or len(candidates) != 1:
        raise FacilityError('No unique general facility map; these controls are read-only.')
    fm = candidates[0]
    hashes = {v.hash for v in fm.flags}
    if len(hashes & ANCHORS) < MIN_ANCHORS or len(hashes) != len(fm.flags):
        raise FacilityError('Facility map needs two unchanged anchors and no duplicate keys.')
    tree = core.SaveTree(f.payload)
    node, user = tree.node_at(fm.start), tree.node_at(users[0].start)
    group = tree.nodes[node].parent if node >= 0 else -1
    if (node < 0 or user < 0 or group < 0 or tree.nodes[node].struct
            or not tree.nodes[group].struct or tree.nodes[group].parent != user
            or any(n.parent == node for n in tree.nodes)):
        raise FacilityError('Unrecognised facility map structure; editing is disabled.')
    return fm


def read(f):
    return {v.hash: v.value for v in locate(f).flags}


def enabled(h, value):
    """Logical switch only, not a prediction that the facility is usable."""
    if value not in (None, 0, 1):
        return None
    active = value == 1
    return not active if catalog()[h]['polarity'] == 'restriction' else active


def state_label(h, value):
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
    fm = locate(f)
    present = {v.hash: v.value for v in fm.flags}
    effective = {}
    for h, state in edits.items():
        old = enabled(h, present.get(h))
        if old is None:
            raise FacilityError(f'{cat[h]["label"]} has an unknown saved value; batch unchanged.')
        if old != state:
            active = not state if cat[h]['polarity'] == 'restriction' else state
            effective[h] = 1 if active else None
    if not effective:
        return bytearray(f.payload)
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
        raise FacilityError('The general flag map is full.')
    body = bytes([f.payload[fm.start + 4]]) + struct.pack('<H', len(records)) + b''.join(records)
    return core.replace_content(f, fm.start, body)
