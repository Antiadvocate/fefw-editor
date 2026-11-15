"""Build the isolated 17 -> 20 Hours Played probe from the accepted baseline.

The source and any existing destination are never overwritten. This changes
only the Deed counter, not reward states, Karma, or any separate play clock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import deeds
import fefw_core as core
import fefw_save as container

BASELINE_SHA256 = '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663'
HOURS = 0xeb92a0f6
TEN_HOUR_CLAIM = 0xe0de8be2
TWENTY_HOUR_CLAIM = 0x71725a0a


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build_probe(source: Path, output: Path) -> dict:
    original = source.read_bytes()
    require(hashlib.sha256(original).hexdigest() == BASELINE_SHA256,
            'Use the accepted Auto from B0-01-Unit-Selection-Test-1.zip.')
    require(not output.exists(), 'Choose a new output directory; nothing is overwritten.')
    require(core.id_hash('実績_プレイ時間') == HOURS, 'Unexpected Hours Played identity.')
    box = container.SaveFile(str(source))
    require(box.verify() == [], 'Source checksum failure.')
    before = core.SaveFile(box.payload)
    core.SaveTree(before.payload)
    values = deeds.read(before)
    require(values.get(HOURS) == 17 and values.get(TEN_HOUR_CLAIM) == 4
            and values.get(TWENTY_HOUR_CLAIM) is None, 'Unexpected baseline Hours/claim state.')
    marker = next(fl for fl in deeds.locate(before).flags if fl.hash == HOURS)
    payload = deeds.edited(before, HOURS, 20)
    changed = [i for i, (a, b) in enumerate(zip(before.payload, payload)) if a != b]
    require(len(payload) == len(before.payload) and changed == [marker.offset],
            'The probe must change only the Hours counter byte.')
    expected = bytearray(payload)
    core.fix_embedded_hashes(expected)
    checksums = [i for i, (a, b) in enumerate(zip(payload, expected)) if a != b]
    box.payload = payload
    serialized = box.to_bytes()
    output.mkdir(parents=True)
    target = output / 'Auto'
    target.write_bytes(serialized)
    reopened = container.SaveFile(str(target))
    require(reopened.verify() == [], 'Generated checksum failure.')
    require(reopened.payload == expected, 'Unexpected serialization changes.')
    after = core.SaveFile(reopened.payload)
    core.SaveTree(after.payload)
    require(deeds.read(after) == values | {HOURS: 20}, 'Unexpected Deed/claim change.')
    require([after.u32(core.user_data(after) + offset)
             for offset in (core.GOLD_AT, core.RENOWN_AT, core.KARMA_AT)] == [1523, 6640, 410],
            'Currency changed.')
    require(source.read_bytes() == original, 'Source baseline changed.')
    report = {
        'status': 'Experimental; game completion, recalculation and claims unverified',
        'source_sha256': BASELINE_SHA256,
        'output': 'Auto', 'output_sha256': hashlib.sha256(serialized).hexdigest(),
        'bytes': len(serialized),
        'counter': {'name': '実績_プレイ時間', 'hash': 'eb92a0f6',
                    'before': 17, 'after': 20, 'payload_offset': marker.offset,
                    'wide_encoding': marker.wide},
        'payload_byte_changes_before_checksum_refresh': changed,
        'embedded_checksum_refresh_offsets': checksums,
        'claims': {'10_hours': 4, '20_hours': None},
        'resources': {'gold': 1523, 'renown': 6640, 'karma': 410},
        'expected_20_hour_reward_if_offered': 20,
        'checks': ['Source/output checksums and object trees valid',
                   'Only one Hours counter value byte changes before checksum refresh',
                   'Header, play-clock bytes, units, all other flags and claims preserved',
                   'Currency preserved; accepted source is byte-identical'],
    }
    (output / 'probe-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_probe(args.source, args.output), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
