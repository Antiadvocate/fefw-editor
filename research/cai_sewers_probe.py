"""Research-only single-record Sewers access probe on Cai's natural Ch4 return.

The entrance checks IsAlreadyRead for a Chapter 2 dialogue. The matching key
is absent from the supplied saves. The dialogue-history map is identified by
its member key and known dialogue anchors, never by its enumerated index.
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

SOURCE_SHA256 = '968a783fbce421e0b0abf3e92cb493de5cb4aa2310437bd62c843d4f27026ef9'
DIALOGUE = 'MID_LGV_1KAI_c02_LG11_003_m06'
READ_HASH = 0x7d18367a
MAP_KEY = 0xb631f2c1
ANCHORS = frozenset(core.id_hash(s) for s in (
    'MID_EV11_000_m01', 'MID_EV11_019_m01', 'MID_LGV_1KAI_c04_LG11_007_m01'))
CASE = 'C4-Sewers-Dialogue-Read'


def locate(f):
    tree=core.SaveTree(f.payload);users=[b for b in f.blocks if b.name=='GameUserData']
    if len(users)!=1:raise core.SaveError('Expected one GameUserData')
    user=tree.node_at(users[0].start);hits=[]
    for fm in core.flag_maps(f):
        records={v.hash:v.value for v in fm.flags}
        if not ANCHORS <= records.keys():continue
        if len(records)!=len(fm.flags) or any(records[k]!=1 for k in ANCHORS):
            raise core.SaveError('Unknown or duplicated dialogue anchors')
        node=tree.node_at(fm.start)
        if node<0 or tree.nodes[node].struct:continue
        parent=tree.nodes[node].parent
        if parent<0 or not tree.nodes[parent].struct or tree.nodes[parent].parent!=user:continue
        at=tree.nodes[parent].start;table=f.ptr(at);count=f.u32(at)>>24
        rows=[(f.u32(table+8*i),f.ptr(table+8*i+4)) for i in range(count)]
        if [v for k,v in rows if k==MAP_KEY]!=[fm.start]:continue
        hits.append(fm)
    if len(hits)!=1:raise core.SaveError('No unique anchored dialogue-history map')
    return hits[0]


def candidate(f):
    info=start.validate(f)
    if (info.route,info.part,info.chapter,info.sequence)!=(1,1,4,0xd63bb68c219adbe2):
        raise core.SaveError('Use the Cai Chapter 4 first-objective state')
    if core.id_hash(DIALOGUE)!=READ_HASH:raise core.SaveError('Dialogue identity mismatch')
    if any(v.hash==READ_HASH for m in core.flag_maps(f) for v in m.flags):
        raise core.SaveError('Dialogue key already present; preserve the supplied state')
    return core.flag_add(f,locate(f),READ_HASH,1)


def build(source, output):
    source,output=Path(source),Path(output)
    if output.exists():raise ValueError('Use a fresh output directory')
    raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Use the unchanged natural Chapter 4 arrival from Cai Test 3')
    box=container.SaveFile(str(source))
    if box.verify():raise ValueError('Source checksums failed')
    f=core.SaveFile(box.payload);story.check_outer(box.raw,start.validate(f))
    box.payload=candidate(f);data=box.to_bytes();g=core.SaveFile(box.payload)
    target=locate(g);fl=next(v for v in target.flags if v.hash==READ_HASH)
    restored=core.SaveFile(core.flag_remove(g,target,fl))
    if start.normalized_blocks(restored)!=start.normalized_blocks(f):
        raise ValueError('Something beyond the single dialogue record changed')
    output.mkdir(parents=True)
    for name,content in (('00-Control-Natural-Chapter-04',raw),(CASE,data)):
        folder=output/name;folder.mkdir();path=folder/'Auto';path.write_bytes(content)
        reopened=container.SaveFile(str(path))
        if reopened.verify():raise ValueError('Output checksums failed')
        if name==CASE and bytes(reopened.payload)!=bytes(box.payload):
            raise ValueError('Serializer roundtrip changed the candidate')
    if source.read_bytes()!=raw:raise ValueError('Source changed')
    info=story.read(g)
    report={'source_sha256':SOURCE_SHA256,'case':CASE,'sha256':hashlib.sha256(data).hexdigest(),
            'bytes':len(data),'route':'Cai','chapter':4,'sequence':f'{info.sequence:016x}',
            'clock':struct.unpack_from('<H5B',g.payload,info.header+22),
            'edit':{'dialogue':DIALOGUE,'hash':f'{READ_HASH:08x}','map_member':f'{MAP_KEY:08x}','value':1},
            'evidence':'Inferred dialogue-history mapping; entrance and progression game test pending'}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.source,a.output),indent=2))
