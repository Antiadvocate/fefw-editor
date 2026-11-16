"""Build the first Cai chapter probes from the fingerprinted native Cai Auto."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import story
import story_start

SOURCE_SHA256 = 'bbb1627a13bb6fddbbf6d35388f0bc1562cbd58372eb3c128392284a8daf1ce1'


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('Use a fresh output directory')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('Use the unchanged native Cai Auto supplied for Test 1')
    box = container.SaveFile(str(source))
    if box.verify():
        raise ValueError('Source checksums failed')
    f = core.SaveFile(box.payload)
    info = story_start.validate(f)
    story.check_outer(box.raw, info)
    if (info.route, info.part, info.chapter) != (1, 1, 2):
        raise ValueError('Expected the native Cai Part 1 Chapter 2 source')
    ready = []
    for chapter in (2, 4, 9):
        target = container.SaveFile(str(source))
        target.payload = story_start.edited(f, chapter)
        ready.append((chapter, target.to_bytes(), bytes(target.payload)))
    output.mkdir(parents=True)
    (output/'00-Control').mkdir()
    (output/'00-Control/Auto').write_bytes(raw)
    records = []
    for chapter, data, payload in ready:
        name = f'CAI1-{chapter:02d}-Chapter-{chapter:02d}'
        folder = output/name; folder.mkdir()
        path = folder/'Auto'; path.write_bytes(data)
        reopened = container.SaveFile(str(path))
        assert reopened.verify() == [] and bytes(reopened.payload) == payload
        check = story_start.validate(core.SaveFile(reopened.payload))
        assert (check.route, check.part, check.chapter) == (1, 1, chapter)
        assert reopened.raw[40:43] == bytes((1, 1, chapter))
        assert reopened.raw[48:57] == payload[check.header+20:check.header+29]
        assert int.from_bytes(reopened.raw[73:81], 'little') == story.sequence(chapter, 1)
        records.append({'case':name, 'chapter':chapter, 'bytes':len(data),
                        'sha256':hashlib.sha256(data).hexdigest(), 'evidence':'Inferred; game test pending'})
    assert source.read_bytes() == raw
    report = {'route':'Cai', 'source_sha256':SOURCE_SHA256, 'cases':records}
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
