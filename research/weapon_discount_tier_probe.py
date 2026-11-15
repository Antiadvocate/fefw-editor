"""Build one disposable Weapons Discount tier-2 probe from the accepted baseline.

This is a research generator, not a general Boon editor. Value 2 is a tier
hypothesis awaiting gameplay. Only the exact accepted B0-01 Auto is supported;
the input and any existing output directory are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import blessings
import boons
import deeds
import fast_travel
import fefw_core as core
import fefw_save as container
import audiences
import tutorials

BASELINE_SHA256 = '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663'
LEVEL_KEY_CANDIDATE = '因果報酬_レベル_武器割引'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build_probe(source: Path, output: Path) -> dict:
    original = source.read_bytes()
    require(hashlib.sha256(original).hexdigest() == BASELINE_SHA256,
            'Use the accepted Auto from B0-01-Unit-Selection-Test-1.zip.')
    require(not output.exists(), 'Choose a new output directory; nothing is overwritten.')
    require(core.id_hash(LEVEL_KEY_CANDIDATE) == boons.WEAPONS_PURCHASE,
            'Weapons level-key hypothesis no longer matches the observed hash.')
    require(core.id_hash('因果報酬_レベル_経験値') == boons.EXP_CANDIDATE,
            'EXP cross-check of the level-key pattern failed.')
    group = next(g for g in boons.catalog() if g['name'] == '武器割引')
    require(group['tiers'][1] == {'tier': 2, 'value': 20, 'clear_count': 1, 'cost': 300},
            'Unexpected tier-2 reference data.')

    box = container.SaveFile(str(source))
    require(box.verify() == [], 'Source container checksum failure.')
    before = core.SaveFile(box.payload)
    core.SaveTree(before.payload)
    require(boons.read_observation(before) == {
        'karma_shards': 410, 'exp_candidate': 1, 'exp_disabled': None,
        'weapons_purchase': 1, 'weapons_disabled': None,
    }, 'Unexpected baseline Boon state.')
    fm = audiences.locate(before)
    marker = next(fl for fl in fm.flags if fl.hash == boons.WEAPONS_PURCHASE)
    require(not marker.wide and marker.value == 1, 'Expected a compact level-1 marker.')

    payload = bytearray(before.payload)
    payload[marker.offset] = 2
    require([i for i, (a, b) in enumerate(zip(before.payload, payload)) if a != b]
            == [marker.offset], 'The probe must change exactly one payload byte.')
    require(len(payload) == len(before.payload), 'Payload size changed.')
    edited = core.SaveFile(payload)
    core.SaveTree(edited.payload)
    require(boons.read_observation(edited)['weapons_purchase'] == 2,
            'The candidate level did not read back as 2.')
    # Existing accepted GUI remains conservative until this experiment returns.
    require(bool(boons.weapons_edit_reason(boons.read_observation(edited))),
            'The current first-tier control must refuse this unaccepted state.')

    expected = bytearray(payload)
    core.fix_embedded_hashes(expected)
    checksum_offsets = [i for i, (a, b) in enumerate(zip(payload, expected)) if a != b]
    box.payload = payload
    serialized = box.to_bytes()
    output.mkdir(parents=True)
    target = output / 'Auto'
    target.write_bytes(serialized)
    reread_box = container.SaveFile(str(target))
    require(reread_box.verify() == [], 'Generated container checksum failure.')
    require(reread_box.payload == expected,
            'Serialized payload differs from the intended edit and checksum refresh.')
    after = core.SaveFile(reread_box.payload)
    core.SaveTree(after.payload)

    def flag_values(f):
        return [[(fl.hash, fl.wide, fl.value) for fl in m.flags]
                for m in core.flag_maps(f)]

    flags = flag_values(before)
    flags[fm.index] = [(h, wide, 2 if h == boons.WEAPONS_PURCHASE else value)
                       for h, wide, value in flags[fm.index]]
    require(flag_values(after) == flags, 'An unrelated flag changed.')
    require(after.units() == before.units(), 'Unit data changed.')
    numbers = [(u.person, core.gear(before, u).unit_number) for u in before.units()]
    require(len(numbers) == len({n for _, n in numbers}) == 9,
            'Expected nine distinct accepted unit numbers.')
    require([(u.person, core.gear(after, u).unit_number) for u in after.units()] == numbers,
            'A repaired unit number changed.')
    for module in (deeds, tutorials, fast_travel):
        require(module.read(after) == module.read(before), module.__name__ + ' changed.')

    def blessing_values(f):
        table = blessings.read(f)
        return table.divine_sand, [(r.hash, r.exp, r.selected) for r in table.records]

    require(blessing_values(after) == blessing_values(before), 'Blessings changed.')
    ud = core.user_data(after)
    require([after.u32(ud + x) for x in (core.GOLD_AT, core.RENOWN_AT, core.KARMA_AT)]
            == [1523, 6640, 410], 'Currency changed.')
    state = boons.read_observation(after)
    require(state == {'karma_shards': 410, 'exp_candidate': 1, 'exp_disabled': None,
                      'weapons_purchase': 2, 'weapons_disabled': None},
            'Unexpected resulting Boon state.')
    require(source.read_bytes() == original, 'The accepted baseline changed.')

    report = {
        'status': 'Experimental; 20% effect, eligibility behavior and persistence await gameplay',
        'source': 'Auto from the accepted B0-01-Unit-Selection-Test-1.zip',
        'source_sha256': BASELINE_SHA256,
        'output': 'Auto', 'bytes': len(serialized),
        'output_sha256': hashlib.sha256(serialized).hexdigest(),
        'change': {'hash': f'{marker.hash:08x}', 'candidate_name': LEVEL_KEY_CANDIDATE,
                   'payload_offset': marker.offset, 'before': 1, 'after': 2},
        'payload_byte_changes_before_checksum_refresh': 1,
        'checksum_refresh_offsets': checksum_offsets,
        'resources': {'gold': 1523, 'renown': 6640, 'karma': 410},
        'unit_numbers': [n for _, n in numbers],
        'checks': [
            'Source and output checksums and object trees valid',
            'Exactly one compact live marker changes from 1 to 2',
            'Every other payload byte preserved before checksum refresh',
            'All other flags, progression, shops, Kalla gate and stables state preserved',
            'Nine distinct unit numbers and all parsed unit data preserved',
            'EXP On, currency, Deeds, tutorials, travel and blessings preserved',
            'Serialized payload equals intended edit plus checksum refresh',
            'Current first-tier editor control correctly refuses the candidate state',
            'Accepted baseline unchanged',
        ],
    }
    (output / 'changes.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                                       encoding='utf8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_probe(args.input, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
