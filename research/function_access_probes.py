"""Cai Test 2: isolated function edits on fingerprinted game-returned saves.

The first-free-time prerequisite is research-only. It is deliberately absent
from the editor's allowlist and no production chapter edit grants it.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import facilities
import fefw_core as core
import fefw_save as container
import story

SOURCES = {
    4: ('CAI1-04-Chapter-04/Auto', '2a8203fa15e740076941a6e157fde17da043a9b4264eb27f9540ca7440f8cd35'),
    9: ('CAI1-09-Chapter-09/Auto-after-advancement', '79aa9e1223a7fcb294cc2bc38a7520e93ee24631f3b3b309e5ab1fb4bca2f84c'),
}
FIRST_FREE = core.id_hash('拠点_進行_初回自由行動')
TRAINING, PRACTICE = 0xd70afcb2, 0x728ccd68
UPPER, LOWER = 0x948de8dd, 0x9402533e


def first_free_probe(f):
    fm = facilities.locate(f)
    if facilities.read(f).get(FIRST_FREE) is not None:
        raise ValueError('Expected absent first-free-time prerequisite')
    # Preserve all existing records and rebuild the containing objects safely.
    last = fm.flags[-1]
    end = last.offset + (4 if last.wide else 1)  # Do not append after leaf padding.
    old = bytes(f.payload[fm.start+4:end])
    count = len(fm.flags)
    body = old[:1] + struct.pack('<H', count+1) + old[3:] + struct.pack('<IB', FIRST_FREE, 1)
    return core.replace_content(f, fm.start, body)


def build(returned, output):
    returned, output = Path(returned), Path(output)
    if output.exists(): raise ValueError('Use a fresh output directory')
    sources = {}
    for chapter, (name, sha) in SOURCES.items():
        path = returned/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError('Use the unmodified Cai Test 1 returns')
        box = container.SaveFile(str(path))
        if box.verify(): raise ValueError('Source checksums failed')
        info = story.read(core.SaveFile(box.payload))
        if (info.route, info.part, info.chapter) != (1, 1, chapter):
            raise ValueError('Unexpected source route or chapter')
        sources[chapter] = path
    journal = {h: True for h, row in facilities.catalog().items() if row['kind'] == 'Journal'}
    cases = [
        ('C2-04A-Journal', 4, journal, False),
        ('C2-04B-Journal-Training-Practice', 4, {**journal, TRAINING: True, PRACTICE: True}, False),
        ('C2-04C-Journal-First-Free', 4, journal, True),
        ('C2-04D-Journal-First-Free-Areas', 4, {**journal, UPPER: True, LOWER: True}, True),
        ('C2-09T-Training-Off', 9, {TRAINING: False}, False),
        ('C2-09P-Practice-Off', 9, {PRACTICE: False}, False),
    ]
    ready = []
    for name, chapter, edits, first_free in cases:
        box = container.SaveFile(str(sources[chapter])); before = core.SaveFile(box.payload)
        after = core.SaveFile(facilities.edited(before, edits))
        if first_free: after = core.SaveFile(first_free_probe(after))
        a, b = facilities.read(before), facilities.read(after)
        allowed = set(edits) | ({FIRST_FREE} if first_free else set())
        if {k:v for k,v in a.items() if k not in allowed} != {k:v for k,v in b.items() if k not in allowed}:
            raise ValueError('Unexpected flag change')
        if story.read(before).sequence != story.read(after).sequence:
            raise ValueError('Story sequence changed')
        box.payload = after.payload
        ready.append((name, chapter, edits, first_free, box.to_bytes()))
    output.mkdir(parents=True)
    for chapter, path in sources.items():
        folder = output/f'00-Control-Chapter-{chapter:02d}'; folder.mkdir()
        (folder/'Auto').write_bytes(path.read_bytes())
    records = []
    for name, chapter, edits, first_free, raw in ready:
        folder = output/name; folder.mkdir(); path = folder/'Auto'; path.write_bytes(raw)
        box = container.SaveFile(str(path))
        if box.verify(): raise ValueError('Output checksums failed')
        records.append({'case':name, 'chapter':chapter, 'bytes':len(raw),
                        'sha256':hashlib.sha256(raw).hexdigest(),
                        'switches':{f'{h:08x}':state for h,state in edits.items()},
                        'research_only_first_free':first_free})
    report = {'source_hashes':{str(k):v[1] for k,v in SOURCES.items()}, 'cases':records}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('returned', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.returned, args.output), indent=2))
