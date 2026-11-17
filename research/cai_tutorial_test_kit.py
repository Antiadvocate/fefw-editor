"""Build the remaining Cai chapter and complete-catalogue tutorial test saves.

Inputs are fingerprinted private captures. Each case is independent; tutorial
cases never change chapter/sequence, and chapter cases never grant tutorials.
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
import story_start as start
import tutorials

SOURCES = {
    'Chapter_Kai_1_1': '2a3eef0be7bab63107e6f7542410f36a999357487fd377912a8c61410e54dfc6',
    'Auto(3)': 'bbb1627a13bb6fddbbf6d35388f0bc1562cbd58372eb3c128392284a8daf1ce1',
    'Auto-arrival': 'fd6b7904195f0a626303f19653459b789503bf2c55de64e1daa4090c78d8309d',
}
CHAPTERS = (1, 4, 5, 6, 7, 8, 10, 11, 12)
FOCUSED = ('TUTO_稽古', 'TUTO_演劇', 'TUTO_テルマエ', 'TUTO_厩舎', 'TUTO_透視')


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
        if (info.route, info.part) != (1, 1): raise ValueError('Expected Cai Part 1')
        originals[name] = raw; saves[name] = f
    pending = []
    for chapter in CHAPTERS:
        source = 'Chapter_Kai_1_1' if chapter == 1 else 'Auto(3)' if chapter == 4 else 'Auto-arrival'
        f = saves[source]; p = start.edited(f, chapter); g = core.SaveFile(p)
        # The shared entry engine preserves all other roots; this independent
        # check also makes the only allowed flag change explicit.
        def flags(x): return [[(v.hash,v.value,v.wide) for v in m.flags] for m in core.flag_maps(x)]
        expected = core.SaveFile(facilities.edited(f, {facilities.SEWERS: True})) if chapter >= 3 else f
        if flags(g) != flags(expected): raise ValueError('Unexpected chapter flag change')
        if tutorials.read(g) != tutorials.read(f): raise ValueError('Chapter edit changed tutorials')
        i = start.validate(g)
        if (i.route,i.part,i.chapter,i.sequence) != (1,1,chapter,story.sequence(chapter,1)):
            raise ValueError('Incorrect chapter entry')
        if struct.unpack_from('<H',g.payload,i.header+22)[0] != 1449:
            raise ValueError('Cai entry has the wrong year')
        pending.append((f'C5-{chapter:02d}-Chapter-{chapter:02d}', source, p, 'chapter-entry'))
    source = 'Auto-arrival'; f = saves[source]
    sets = (
        ('TUT5-01-Focused', {core.id_hash(name): 2 for name in FOCUSED}),
        ('TUT5-02-All-218', {h: 2 for h in tutorials.catalog()}),
        ('TUT5-03-Empty', {h: None for h in tutorials.catalog()}),
    )
    for name, edits in sets:
        p = tutorials.edited(f, edits); g = core.SaveFile(p)
        # Restore just the affected list to prove all unrelated data survives.
        old = tutorials.locate(f); new = tutorials.locate(g)
        restored = core.SaveFile(core.replace_content(g, new.start, bytes(f.payload[old.start+4:f.ptr(old.start)])))
        if start.normalized_blocks(restored) != start.normalized_blocks(f):
            raise ValueError('Tutorial edit changed unrelated data')
        if story.read(g) != story.read(f): raise ValueError('Tutorial case changed story state')
        pending.append((name, source, p, 'tutorial-only'))
    # Nothing is written until every candidate has been constructed and checked.
    output.mkdir(parents=True)
    for source in SOURCES:
        folder = output/'controls'/source.replace('(', '-').replace(')', '')
        folder.mkdir(parents=True); (folder/'Auto').write_bytes(originals[source])
    records = []
    for name, source, payload, kind in pending:
        box = container.SaveFile(str(source_dir/source));box.payload = payload;data = box.to_bytes()
        folder = output/name;folder.mkdir();path = folder/'Auto';path.write_bytes(data)
        reopened = container.SaveFile(str(path));g = core.SaveFile(reopened.payload);i = story.read(g)
        if reopened.verify() or bytes(reopened.payload) != bytes(payload): raise ValueError('Export roundtrip failed')
        story.check_outer(reopened.raw,i)
        records.append({'case':name,'kind':kind,'source':source,'chapter':i.chapter,
                        'clock':struct.unpack_from('<H5B',g.payload,i.header+22),
                        'sequence':f'{i.sequence:016x}', 'tutorial_records':len(tutorials.read(g)),
                        'sewers':next((v.value for v in facilities.locate_history(g).flags if v.hash==facilities.SEWERS),None),
                        'units':[core.gear(g,u).unit_number for u in g.units()],
                        'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
                        'evidence':'Game test pending'})
    for name, raw in originals.items():
        if (source_dir/name).read_bytes() != raw: raise ValueError('Source was changed')
    result = {'sources':SOURCES,'cases':records}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source_dir',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.source_dir,a.output),indent=2))
