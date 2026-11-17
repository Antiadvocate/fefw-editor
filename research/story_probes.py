"""Create independent Leda P1 chapter probes from one private source slot.

Never overwrites the source or an existing output directory. No saves belong
in Git. Invoke with a disposable accepted source and a fresh output directory.
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


def build_probes(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('Output already exists; choose a fresh directory.')
    original = source.read_bytes()
    box = container.SaveFile(str(source))
    if box.verify():
        raise ValueError('Source checksum verification failed: ' + ', '.join(box.verify()))
    f = core.SaveFile(box.payload); info = story.require_leda(f); story.check_outer(box.raw, info)
    allowed = {info.header+14, info.user+5, *range(info.header+45,info.header+53), *range(info.user+81,info.user+89)}
    before = bytes(box.payload); prepared = []
    for chapter in story.CHAPTERS:
        box.payload = story.edited(f, chapter)
        data = box.to_bytes()
        if len(box.payload) != len(before) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,box.payload))):
            raise ValueError('Unexpected payload changes outside story fields.')
        prepared.append((chapter,data,bytes(box.payload)))
    output.mkdir(parents=True,exist_ok=False)
    (output/'00-Control').mkdir();(output/'00-Control'/'Auto').write_bytes(original)
    reports=[]
    for chapter,data,expected in prepared:
        folder=output/f'STORY-{chapter:02d}-Leda-P1-Chapter-{chapter:02d}';folder.mkdir()
        slot=folder/'Auto';slot.write_bytes(data)
        check=container.SaveFile(str(slot));assert check.verify()==[]
        after=story.require_leda(core.SaveFile(check.payload))
        assert (after.chapter,after.sequence)==(chapter,story.sequence(chapter))
        assert bytes(check.payload)==expected
        assert check.raw[42]==chapter
        assert int.from_bytes(check.raw[73:81],'little')==after.sequence
        reports.append({'case':folder.name,'chapter':chapter,'sequence':f'{after.sequence:016x}',
                        'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
                        'changed_payload_offsets':[i for i,(a,b) in enumerate(zip(before,expected)) if a!=b],
                        'status':'Checksum/structure/preservation passed; game test pending'})
    assert source.read_bytes()==original
    report={'source_sha256':hashlib.sha256(original).hexdigest(),'source_progress':info.label,
            'scope':'Selected live chapter and sequence only; no prior-progression grants; embedded restart unchanged',
            'cases':reports}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();print(json.dumps(build_probes(args.source,args.output),indent=2))
