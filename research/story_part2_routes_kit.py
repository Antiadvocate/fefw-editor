"""Build 18 independent Part 2 probes from each route's own Part 1 save.

Fingerprint guards identify the agreed private baselines; no private save data
or game binaries belong in Git. Historical Test 1: Chapter 6 retains the
original state before its movement repair.
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
import facilities
import story
import story_start as start

SOURCES = {
    4: ('leda', 9, '6597d0082a38a15310e76a706bb4d5fa67c7029a3a364362f61da111472bb018'),
    2: ('dietrich', 4, '1e2f3793aa3d70960d60e406cd09c84d8c54cf2dada188c0df17a86856b0d652'),
    3: ('theodora', 3, '4e3a74d53b8a5b0ebbe4e13329abbd4f14a00c32134ea2ff38d96a888a6dce78'),
}
ALLOWED_ROOTS = {'Header', 'GameUserData', 'GameSchedule', 'Calendar', 'GameRestartData'}


def build(leda, dietrich, theodora, output):
    paths = {4: Path(leda), 2: Path(dietrich), 3: Path(theodora)}
    output = Path(output)
    if output.exists():
        raise ValueError('Use a fresh output directory')
    ready = []; originals = {}; sources = []
    for route, path in paths.items():
        name, chapter, sha = SOURCES[route]
        raw = path.read_bytes(); box = container.SaveFile(path)
        if hashlib.sha256(raw).hexdigest() != sha or box.verify():
            raise ValueError('Unexpected or invalid baseline: '+name)
        originals[route] = raw
        f = core.SaveFile(box.payload); info = start.validate(f)
        story.check_outer(box.raw, info)
        if (info.route, info.part, info.chapter) != (route, 1, chapter):
            raise ValueError('Unexpected baseline story state')
        original = start.normalized_blocks(f)
        entry = core.SaveFile(start.enter_part2(f))
        sources.append({'route': story.ROUTES[route], 'chapter': chapter,
                        'sha256': sha, 'units': len(f.units())})
        for target in start.chapters_for(route, 2):
            candidate = container.SaveFile(path)
            edit = (lambda f: start._edited_at_entry(f, 6, 1450, start.PART2_DATES[6])) if target == 6 else (lambda f: start.edited(f, target))
            candidate.payload = edit(entry)
            candidate._allow_part_transition = True
            data = candidate.to_bytes()
            g = core.SaveFile(candidate.payload); i = start.validate(g)
            after = start.normalized_blocks(g)
            if original.keys() != after.keys() or any(original[k] != after[k] for k in original.keys()-ALLOWED_ROOTS):
                raise ValueError('Unrelated root changed')
            baseline = core.SaveFile(facilities.edited(f, {start.PART2_UPPER_MOVEMENT: True})) if target == 5 else f
            expected = bytearray(start.normalized_blocks(baseline)['GameUserData'])
            expected[8:10] = bytes((2, target))
            struct.pack_into('<Q', expected, 85, story.sequence(target, route, 2))
            struct.pack_into('<Q', expected, 4+start.RESUME_OFFSET, start.CHECKPOINT_ID)
            if expected != after['GameUserData']:
                raise ValueError('Unexpected player or flag changes')
            if edit(g) != candidate.payload:
                raise ValueError('Entry is not idempotent')
            ready.append((route, target, data, bytes(candidate.payload),
                          [(u.person, core.gear(g, u).unit_number) for u in g.units()]))
    output.mkdir(parents=True)
    for route, raw in originals.items():
        folder = output/story.ROUTES[route]/'00-Part1-Control'; folder.mkdir(parents=True)
        (folder/'Auto').write_bytes(raw)
    records = []
    for route, chapter, raw, payload, units in ready:
        folder = output/story.ROUTES[route]/f'P2-{chapter:02d}-Chapter-{chapter:02d}'
        folder.mkdir(); path = folder/'Auto'; path.write_bytes(raw)
        reopened = container.SaveFile(path); g = core.SaveFile(reopened.payload); i = start.validate(g)
        story.check_outer(reopened.raw, i)
        if reopened.verify() or bytes(reopened.payload) != payload:
            raise ValueError('Serialized save failed validation')
        if (i.route, i.part, i.chapter) != (route, 2, chapter):
            raise ValueError('Wrong route, part or chapter')
        if (reopened.raw[40:43] != bytes((route, 2, chapter)) or
                reopened.raw[48:57] != payload[i.header+20:i.header+29] or
                int.from_bytes(reopened.raw[73:81], 'little') != i.sequence):
            raise ValueError('Outer summary mismatch')
        records.append({'case': str(folder.relative_to(output)), 'route': story.ROUTES[route],
                        'part': 2, 'chapter': chapter, 'sequence': f'{i.sequence:016x}',
                        'sha256': hashlib.sha256(raw).hexdigest(), 'units': units,
                        'game_test': 'pending', 'evidence': 'Inferred shared Part 2 timeline; retained route-specific Part 1 baseline'})
    if any(path.read_bytes() != originals[route] for route, path in paths.items()):
        raise ValueError('Source save changed')
    result = {'sources': sources, 'cases': records,
              'scope': 'Independent Part 1 conversions; not natural Part 2 baselines or full-playthrough acceptance.'}
    (output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('leda', 'dietrich', 'theodora', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    print(json.dumps(build(a.leda, a.dietrich, a.theodora, a.output), indent=2))
