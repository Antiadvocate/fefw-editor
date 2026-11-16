"""Research-only Cai Chapter 3 entry from the passed Chapter 2 advancement.

Use natural play through Chapter 3 to obtain an independent Chapter 4 control.
This does not add a production chapter target or grant progression flags.
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

SOURCE_SHA256 = '3f997fc788a1eb61ee418645d33f4f1dedfb41a382805862c7ff9e120715f963'
ENTRY_CLOCK = (1449, 2, 4, 8, 0, 0)
CASE = 'CAI3-03-Chapter-03'


def candidate(f):
    info = start.validate(f)
    if (info.route, info.part, info.chapter) != (1, 1, 2):
        raise story.StoryError('This research probe needs a Cai Part 1 Chapter 2 source.')
    return start._edited_at_entry(f, 3, ENTRY_CLOCK[0], ENTRY_CLOCK[1:5])


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('Use a fresh output directory')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('Use the unchanged successful Cai Test 1 Chapter 2 advancement return')
    box = container.SaveFile(str(source))
    if box.verify():
        raise ValueError('Source checksums failed')
    before = core.SaveFile(box.payload)
    story.check_outer(box.raw, start.validate(before))
    box.payload = candidate(before)
    data = box.to_bytes()
    after = core.SaveFile(box.payload)
    info = start.validate(after)
    if (info.route, info.part, info.chapter, info.sequence) != (1, 1, 3, story.sequence(3, 1)):
        raise ValueError('Unexpected Chapter 3 entry')
    if struct.unpack_from('<H5B', after.payload, info.header+22) != ENTRY_CLOCK:
        raise ValueError('Unexpected Chapter 3 date')
    def flags(f):
        return [[(v.hash, v.value, v.wide) for v in m.flags] for m in core.flag_maps(f)]
    def units(f):
        return [(u.person, core.gear(f, u).unit_number) for u in f.units()]
    if flags(after) != flags(before) or units(after) != units(before):
        raise ValueError('Unrelated progression or party changed')
    output.mkdir(parents=True)
    (output/'00-Control-Chapter-02').mkdir()
    (output/'00-Control-Chapter-02'/'Auto').write_bytes(raw)
    (output/CASE).mkdir()
    path = output/CASE/'Auto'
    path.write_bytes(data)
    reopened = container.SaveFile(str(path))
    if reopened.verify() or bytes(reopened.payload) != bytes(box.payload):
        raise ValueError('Candidate failed checksum or serializer roundtrip')
    story.check_outer(reopened.raw, info)
    if reopened.raw[48:57] != after.payload[info.header+20:info.header+29]:
        raise ValueError('Outer clock summary disagrees')
    if source.read_bytes() != raw:
        raise ValueError('Source was modified')
    report = {'source_sha256': SOURCE_SHA256, 'case': CASE, 'route': 'Cai',
              'chapter': 3, 'entry_clock': ENTRY_CLOCK,
              'entry_sequence': f'{info.sequence:016x}',
              'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
              'evidence': 'Research only; Chapter 3 and natural Chapter 4 progression untested'}
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
