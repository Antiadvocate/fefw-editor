"""Prepare two Chapter 5 access probes and a separate Part 1-to-2 experiment."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import story
import story_start as start

SOURCE_HASHES = {
    'part1':'fd6b7904195f0a626303f19653459b789503bf2c55de64e1daa4090c78d8309d',
    'part2':'2a87544e8a937f210e200d4503e9e43e7c4f277d783c6b66434a87a47c3a675a',
    'blocked':'ef62eb051ba7e0194b080f4f9d78f701c7fbcfc3daba42fa57ea18196785e15b',
}


def build(part1, part2, blocked, output):
    paths={k:Path(v) for k,v in zip(('part1','part2','blocked'),(part1,part2,blocked))}
    output=Path(output)
    if output.exists():raise ValueError('Choose a new output directory.')
    raws={k:p.read_bytes() for k,p in paths.items()}
    for k,raw in raws.items():
        if hashlib.sha256(raw).hexdigest()!=SOURCE_HASHES[k]:
            raise ValueError('Unexpected '+k+' baseline for Test 2.')
        if container.SaveFile(str(paths[k])).verify():raise ValueError('Invalid '+k+' checksums.')
    jobs=[('05A-Resume-UpperMovement','blocked',start.repair_cai_part2_chapter5,False),
          ('05B-Reenter-UpperMovement','part2',lambda f:start.edited(f,5),False),
          ('X1-Part1-to-Part2','part1',start.enter_cai_part2,True)]
    ready=[]
    for name,key,edit,conversion in jobs:
        box=container.SaveFile(str(paths[key]));original=core.SaveFile(box.payload)
        before=start.normalized_blocks(original)
        box.payload=edit(original)
        box._allow_cai_part_transition=conversion
        data=box.to_bytes();after=start.normalized_blocks(core.SaveFile(box.payload))
        allowed={'GameUserData'} if name.startswith('05A') else {
            'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}
        assert before.keys()==after.keys()
        assert all(before[k]==after[k] for k in before.keys()-allowed)
        ready.append((name,key,data,bytes(box.payload)))
    output.mkdir(parents=True);control=output/'00-Part1-Control';control.mkdir()
    (control/'Auto').write_bytes(raws['part1'])
    records=[]
    for name,key,data,payload in ready:
        folder=output/name;folder.mkdir();path=folder/'Auto';path.write_bytes(data)
        reopened=container.SaveFile(str(path));f=core.SaveFile(reopened.payload);info=start.validate(f)
        assert not reopened.verify() and bytes(reopened.payload)==payload
        assert reopened.raw[40:43]==bytes((info.route,info.part,info.chapter))
        assert reopened.raw[48:57]==payload[info.header+20:info.header+29]
        records.append({'case':name,'source':key,'sha256':hashlib.sha256(data).hexdigest(),
                        'part':info.part,'chapter':info.chapter,'game_test':'pending'})
    assert all(paths[k].read_bytes()==raw for k,raw in raws.items())
    result={'source_sha256':SOURCE_HASHES,'cases':records}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('part1','part2','blocked','output'):p.add_argument(name,type=Path)
    a=p.parse_args();print(json.dumps(build(a.part1,a.part2,a.blocked,a.output),indent=2))
