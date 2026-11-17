"""Build independent Dietrich entry probes from fingerprinted private saves.

No game data or save bytes are bundled with this script. All twelve entries
remain inferred until the player reports opening and progression results.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import story
import story_start as start
import tutorials

SOURCES = {
    'Auto': '1e2f3793aa3d70960d60e406cd09c84d8c54cf2dada188c0df17a86856b0d652',
    'Chapter_Dit_1_1': '0271f021a58e62dd8bf2931c2aab484dbcfe358371922a347b4c50ff27fb213e',
    'Chapter_Dit_1_2': 'c124def0b52827dac594b127c8450eca0ddd310ccd1594a332339bbc711e6d0b',
    'Chapter_Dit_1_3': '06919e7771a7a4401e7891b1d715ccc9720fb644629487d2e6c7b0e74f2f07a8',
    'Chapter_Dit_1_4': '7cba2993960adb6e6345f67951ed3a6ce8ae0157c08d3b2626796265e6a632b4',
}


def flags(f):
    return [[(v.hash, v.value, v.wide) for v in m.flags] for m in core.flag_maps(f)]


def build(source_dir, output):
    source_dir, output = Path(source_dir), Path(output)
    if output.exists(): raise ValueError('Use a fresh output directory')
    originals = {}; saves = {}
    for name, sha in SOURCES.items():
        raw = (source_dir/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha: raise ValueError('Wrong source: '+name)
        box = container.SaveFile(str(source_dir/name))
        if box.verify(): raise ValueError('Source checksums failed: '+name)
        f = core.SaveFile(box.payload); info = start.validate(f); story.check_outer(box.raw, info)
        if (info.route, info.part) != (2, 1): raise ValueError('Expected Dietrich Part 1')
        if name != 'Auto':
            chapter = int(name.rsplit('_', 1)[1])
            if info.chapter != chapter or info.sequence != story.sequence(chapter, 2):
                raise ValueError('Native checkpoint disagrees with the inferred rule')
            if struct.unpack_from('<H5B', f.payload, info.header+22) != (1449, *start.target(chapter, 2), 0):
                raise ValueError('Native checkpoint disagrees with the entry date')
        originals[name] = raw; saves[name] = f
    pending = []
    for chapter in range(1, 13):
        source = 'Chapter_Dit_1_1' if chapter == 1 else 'Auto'
        f = saves[source]
        # Reproduce the original Test 1 profile, before Test 2 prerequisites.
        payload = start._edited_at_entry(f, chapter, 1449, start.target(chapter, 2))
        g = core.SaveFile(payload)
        if flags(g) != flags(f) or tutorials.read(g) != tutorials.read(f):
            raise ValueError('Chapter edit changed flags or tutorials')
        original = start.normalized_blocks(f); after = start.normalized_blocks(g)
        allowed = {'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}
        if any(original[k] != after[k] for k in original.keys()-allowed):
            raise ValueError('Chapter edit changed an unrelated root')
        i = start.validate(g)
        if (i.route,i.part,i.chapter,i.sequence) != (2,1,chapter,story.sequence(chapter,2)):
            raise ValueError('Incorrect chapter entry')
        if start._edited_at_entry(g, chapter, 1449, start.target(chapter, 2)) != payload: raise ValueError('Entry is not idempotent')
        pending.append((f'D1-{chapter:02d}-Chapter-{chapter:02d}', source, payload))
    output.mkdir(parents=True)
    control = output/'00-Native-Control'; control.mkdir()
    for name, raw in originals.items(): (control/name).write_bytes(raw)
    records = []
    for name, source, payload in pending:
        box = container.SaveFile(str(source_dir/source)); box.payload = payload; data = box.to_bytes()
        folder = output/name; folder.mkdir(); path = folder/'Auto'; path.write_bytes(data)
        reopened = container.SaveFile(str(path)); g = core.SaveFile(reopened.payload); i = start.validate(g)
        if reopened.verify() or bytes(reopened.payload) != bytes(payload): raise ValueError('Export roundtrip failed')
        if (reopened.raw[40:43] != bytes((2,1,i.chapter)) or
                int.from_bytes(reopened.raw[73:81], 'little') != i.sequence or
                reopened.raw[48:57] != payload[i.header+20:i.header+29]):
            raise ValueError('Export summary mismatch')
        records.append({'case':name, 'source':source, 'chapter':i.chapter,
                        'clock':struct.unpack_from('<H5B', g.payload, i.header+22),
                        'sequence':f'{i.sequence:016x}', 'tutorial_records':len(tutorials.read(g)),
                        'units':[core.gear(g,u).unit_number for u in g.units()],
                        'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data),
                        'evidence':'Inferred — game test pending'})
    for name, raw in originals.items():
        if (source_dir/name).read_bytes() != raw: raise ValueError('Source was changed')
    result = {'route':'Dietrich', 'sources':SOURCES, 'cases':records}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source_dir',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.source_dir,a.output),indent=2))
