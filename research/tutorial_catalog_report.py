"""Inventory tutorial identities and title IDs from a private GameData dump.

Only metadata is reported. Localized message bodies are not bundled or read.
The editor never needs GameData at runtime.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fefw_core as core


def report(gamedata):
    sources = []; entries = {}
    for filename in ('Tutorial.bin', 'Tutorial_P0.bin'):
        b = (Path(gamedata)/filename).read_bytes()
        def q(at):
            if at < 0 or at+8 > len(b): raise ValueError('Invalid tutorial pointer')
            return struct.unpack_from('<Q', b, at)[0]
        def string(pointer):
            at = pointer+32
            if not pointer or not 32 <= at < len(b): raise ValueError('Invalid string pointer')
            return b[at:b.index(0, at)].decode('utf8')
        begin = 0x180
        end = q(begin+32)+32
        if not begin < end < len(b) or (end-begin) % 48:
            raise ValueError('Unknown tutorial group layout')
        count = 0
        for at in range(begin, end, 48):
            name = string(q(at+8))
            # U+3000 inside a real identity is valid; do not use isprintable().
            if not name.startswith('TUTO_'): raise ValueError('Unknown tutorial group')
            row = q(at+32)+32
            if row < end or string(q(row+8)) != name:
                raise ValueError('Tutorial child identity mismatch')
            title = string(q(row+40))
            if not title.startswith('MID_TUT_'): raise ValueError('Unknown title identifier')
            category_id = struct.unpack_from('<I', b, row+32)[0]
            if category_id not in range(1, 7): raise ValueError('Unknown tutorial category')
            h = f'{core.id_hash(name):08x}'
            if h in entries: raise ValueError('Duplicate tutorial identity')
            entries[h] = {'name': name, 'title_id': title, 'source': filename,
                          'offset': f'0x{at:x}', 'category_id': category_id}
            count += 1
        sources.append({'name': filename, 'sha256': hashlib.sha256(b).hexdigest(), 'entries': count})
    return {'sources': sources, 'entries': entries,
            'scope': 'Complete identities in the supplied two tables; title IDs are not localized English titles.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('gamedata', type=Path)
    print(json.dumps(report(p.parse_args().gamedata), ensure_ascii=False, indent=2))
