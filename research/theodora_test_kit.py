"""Build Theodora replay probes from fingerprinted private reference saves.

All twelve targets use the same Chapter 3 Auto, including backward replay of
Chapters 1/2. Native controls are never edited. No private bytes are bundled
with this script, and structural validation is not game acceptance.
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
    'Auto': '4e3a74d53b8a5b0ebbe4e13329abbd4f14a00c32134ea2ff38d96a888a6dce78',
    'Chapter_Seo_1_1': '6801950515512668d86b82a998e58575dcf8e0a74a4594b91207cb5659b6532f',
    'Chapter_Seo_1_2': '5040fc94d41b79e922a28c2a7b86da139e7d0d040ea0bffe7d7c2cbd93f5fe1e',
    'Chapter_Seo_1_3': '57f8010cebd47e5b5b36922e9ab1b00ce29dc0398a3e35303e7d7245bdf444e9',
}
NATIVE_CLOCKS = {1: (1446, 2, 1, 12, 0, 0), 2: (1446, 2, 13, 12, 0, 0),
                 3: (1449, 2, 4, 7, 0, 0)}


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
        if (info.route, info.part) != (3, 1): raise ValueError('Expected Theodora Part 1')
        if name != 'Auto':
            chapter = int(name.rsplit('_', 1)[1])
            if info.chapter != chapter or info.sequence != story.sequence(chapter, 3):
                raise ValueError('Native checkpoint disagrees with the inferred rule')
            if struct.unpack_from('<H5B', f.payload, info.header+22) != NATIVE_CLOCKS[chapter]:
                raise ValueError('Native checkpoint disagrees with the entry date')
        originals[name] = raw; saves[name] = f
    f = saves['Auto']; original = start.normalized_blocks(f); pending = []
    for chapter in range(1, 13):
        payload = start.edited(f, chapter); g = core.SaveFile(payload)
        if flags(g) != flags(f) or tutorials.read(g) != tutorials.read(f):
            raise ValueError('Chapter edit changed flags or tutorials')
        after = start.normalized_blocks(g)
        allowed = {'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}
        if original.keys() != after.keys() or any(original[k] != after[k] for k in original.keys()-allowed):
            raise ValueError('Chapter edit changed an unrelated root')
        i = start.validate(g)
        if (i.route,i.part,i.chapter,i.sequence) != (3,1,chapter,story.sequence(chapter,3)):
            raise ValueError('Incorrect chapter entry')
        if struct.unpack_from('<H5B', g.payload, i.header+22) != (start.THEODORA_YEARS[chapter], *start.THEODORA_DATES[chapter], 0):
            raise ValueError('Incorrect entry clock')
        if start.edited(g, chapter) != payload: raise ValueError('Entry is not idempotent')
        pending.append((f'T1-{chapter:02d}-Chapter-{chapter:02d}', payload))
    output.mkdir(parents=True)
    control = output/'00-Native-Control'; control.mkdir()
    for name, raw in originals.items(): (control/name).write_bytes(raw)
    # Ready-to-load controls retain every byte; only the filename becomes Auto.
    for chapter in range(1, 4):
        folder = output/f'Control-Chapter-{chapter:02d}'; folder.mkdir()
        (folder/'Auto').write_bytes(originals[f'Chapter_Seo_1_{chapter}'])
    records = []
    for name, payload in pending:
        box = container.SaveFile(str(source_dir/'Auto')); box.payload = payload; data = box.to_bytes()
        folder = output/name; folder.mkdir(); path = folder/'Auto'; path.write_bytes(data)
        reopened = container.SaveFile(str(path)); g = core.SaveFile(reopened.payload); i = start.validate(g)
        if reopened.verify() or bytes(reopened.payload) != bytes(payload): raise ValueError('Export roundtrip failed')
        if (reopened.raw[40:43] != bytes((3,1,i.chapter)) or
                int.from_bytes(reopened.raw[73:81], 'little') != i.sequence or
                reopened.raw[48:57] != payload[i.header+20:i.header+29]):
            raise ValueError('Export summary mismatch')
        records.append({'case':name, 'source':'Auto', 'chapter':i.chapter,
                        'clock':struct.unpack_from('<H5B', g.payload, i.header+22),
                        'sequence':f'{i.sequence:016x}', 'tutorial_records':len(tutorials.read(g)),
                        'units':[core.gear(g,u).unit_number for u in g.units()],
                        'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data),
                        'evidence':'Inferred — game test pending'})
    for name, raw in originals.items():
        if (source_dir/name).read_bytes() != raw: raise ValueError('Source was changed')
    result = {'route':'Theodora', 'sources':SOURCES, 'cases':records,
              'controls':'Chapter 1–3 native files also copied unchanged as Control-Chapter-XX/Auto'}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source_dir',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.source_dir,a.output),indent=2))
