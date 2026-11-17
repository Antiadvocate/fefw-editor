"""Build provisional Cai Part 2 cases from the supplied natural free-time save.

Private saves are inputs/outputs only, never repository fixtures. Every candidate
uses the same editor writer and serializer as the UI; no broad flag resets.
"""
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

BASELINE_SHA256 = '2a87544e8a937f210e200d4503e9e43e7c4f277d783c6b66434a87a47c3a675a'


def build(source, output):
    source, output = Path(source), Path(output)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA256:
        raise ValueError('Use the unchanged Cai Part 2 first-control baseline for Test 1.')
    if output.exists():
        raise ValueError('Use a fresh output directory.')
    box = container.SaveFile(str(source)); f = core.SaveFile(box.payload)
    info = story_start.validate(f)
    if box.verify() or (info.route,info.part,info.chapter)!=(1,2,1):
        raise ValueError('Unexpected baseline state or checksums.')
    story.check_outer(box.raw, info)
    ready=[]
    for chapter in story.PART2_CHAPTERS:
        candidate=container.SaveFile(str(source))
        candidate.payload=story_start._edited_at_entry(f,chapter,1450,story_start.PART2_DATES[chapter])
        data=candidate.to_bytes()
        ready.append((chapter,data,bytes(candidate.payload)))
    output.mkdir(parents=True)
    (output/'00-Native-Arrival').mkdir()
    (output/'00-Native-Arrival'/'Auto').write_bytes(raw)
    cases=[]
    for chapter,data,payload in ready:
        folder=output/f'P2-{chapter:02d}-Chapter-{chapter:02d}'
        folder.mkdir();path=folder/'Auto';path.write_bytes(data)
        reopened=container.SaveFile(str(path));g=core.SaveFile(reopened.payload)
        i=story_start.validate(g)
        assert not reopened.verify() and bytes(reopened.payload)==payload
        assert (i.route,i.part,i.chapter)==(1,2,chapter)
        assert reopened.raw[48:57]==payload[i.header+20:i.header+29]
        assert int.from_bytes(reopened.raw[73:81],'little')==i.sequence
        cases.append({'case':folder.name,'chapter':chapter,'sequence':f'{i.sequence:016x}',
                      'sha256':hashlib.sha256(data).hexdigest(),'game_test':'pending',
                      'sequence_evidence':'captured checkpoint' if chapter==1 else 'inferred suffix pattern'})
    assert source.read_bytes()==raw
    result={'baseline_sha256':BASELINE_SHA256,'route':'Cai','part':2,'cases':cases}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.source,a.output),indent=2))
