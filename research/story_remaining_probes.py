"""Prepare the seven remaining chapter tests using the actual editor engine."""
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

BASELINE_SHA256 = '8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663'


def build(source, output, *, chapters=(5, 6, 7, 8, 10, 11, 12), prefix='ST4'):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('Use a fresh output directory')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA256:
        raise ValueError('Use the unchanged accepted B0-01 baseline for this test set')
    original = container.SaveFile(str(source))
    if original.verify():
        raise ValueError('Invalid source checksums')
    f = core.SaveFile(original.payload)
    info = story_start.validate(f)
    story.check_outer(original.raw, info)
    ready = []
    # Freeze this historical Test 4 set as evidence labels change in the UI.
    for chapter in chapters:
        box = container.SaveFile(str(source))
        box.payload = story_start.edited(f, chapter)
        ready.append((chapter, box.to_bytes(), bytes(box.payload)))
    output.mkdir(parents=True)
    (output/'00-Control').mkdir()
    (output/'00-Control/Auto').write_bytes(raw)
    records = []
    for chapter, data, payload in ready:
        name = f'{prefix}-{chapter:02d}-Chapter-{chapter:02d}'
        folder = output/name
        folder.mkdir()
        path = folder/'Auto'
        path.write_bytes(data)
        box = container.SaveFile(str(path))
        assert box.verify() == [] and bytes(box.payload) == payload
        check = story_start.validate(core.SaveFile(box.payload))
        assert check.chapter == chapter
        assert box.raw[48:57] == box.payload[check.header+20:check.header+29]
        records.append({'case':name,'chapter':chapter,'sha256':hashlib.sha256(data).hexdigest(),
                        'bytes':len(data),'evidence':'Inferred; game test pending'})
    assert source.read_bytes() == raw
    report = {'source_sha256':BASELINE_SHA256,'cases':records}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('output',type=Path)
    a = p.parse_args()
    print(json.dumps(build(a.source,a.output),indent=2))
