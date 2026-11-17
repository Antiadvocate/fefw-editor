"""Focused Chapter 2 diagnostics and integrated Chapter 5/6 entry checks.

Private inputs are fingerprinted. No private bytes are embedded. The unnamed
event-store keys below are candidates, not established engine identities.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fefw_core as core
import fefw_save as container
import story
import story_start as start
import story_prerequisites as pre
import tutorials
from research.dietrich_retry_kit import flag_snapshot, HISTORY, RESCUE
from research.dietrich_test_kit import SOURCES

BLOCKED_SHA = '56a871a45bd634f3f9d023713ee5e8c8b536db71774c0d1d4f75e38164764bed'
NATIVE_PROGRESS_SHA = 'e69ec7d0a7aac0d69d06fd9d885c4ee733cffa5404372849df44865096d6f431'
EVENT_MEMBER = 0x06c136c7
EVENT_CANDIDATE = 0xbe852456
TIME_CANDIDATE = 0x370344f7


def remove_exact(f, member, key, value, wide):
    fm = pre.member_map(f,member)
    hits = [v for v in fm.flags if v.hash == key]
    if len(hits) != 1 or (hits[0].value,hits[0].wide) != (value,wide):
        raise core.SaveError('Diagnostic source record differs from its capture.')
    return core.SaveFile(core.flag_remove(f,fm,hits[0]))


def read_source(path, sha):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha: raise ValueError('Wrong source: '+str(path))
    box = container.SaveFile(str(path)); f=core.SaveFile(box.payload)
    if box.verify(): raise ValueError('Source checksum failure')
    info=start.validate(f);story.check_outer(box.raw,info)
    if (info.route,info.part)!=(2,1): raise ValueError('Wrong source route')
    return f,raw


def build(returns1, returns2, test1, output):
    returns1,returns2,test1,output=map(Path,(returns1,returns2,test1,output))
    if output.exists(): raise ValueError('Use a fresh output directory')
    native=test1/'test-saves/00-Native-Control'
    paths={
        'blocked':returns1/'D1-02-Chapter-02/Auto',
        'chapter4':native/'Auto',
        'native2':native/'Chapter_Dit_1_2',
        'native_progress':returns2/'D2-02C-Native-control/Auto-after-progress',
    }
    hashes={'blocked':BLOCKED_SHA,'chapter4':SOURCES['Auto'],
            'native2':SOURCES['Chapter_Dit_1_2'],'native_progress':NATIVE_PROGRESS_SHA}
    saves={};originals={}
    for name,path in paths.items(): saves[name],originals[name]=read_source(path,hashes[name])
    # Both candidates appeared between the untouched native control and its
    # successful rescue return. That association does not decode their meaning.
    before,after=flag_snapshot(saves['native2']),flag_snapshot(saves['native_progress'])
    for h,value,wide in ((EVENT_CANDIDATE,1,False),(TIME_CANDIDATE,80202012,True)):
        key=f'{EVENT_MEMBER:08x}:{h:08x}'
        if key in before or after.get(key)!=[value,wide]: raise ValueError('Candidate evidence mismatch')
    a=remove_exact(saves['blocked'],EVENT_MEMBER,EVENT_CANDIDATE,1,False)
    b=remove_exact(a,HISTORY,core.id_hash(RESCUE),1,False)
    c=remove_exact(b,EVENT_MEMBER,TIME_CANDIDATE,80202012,True)
    plans=[
        ('D3-02A-Event-candidate','blocked',a,'Clear one unnamed event-store flag; keep rescue dialogue history.'),
        ('D3-02B-Event-and-history','blocked',b,'02A plus clear the rescue dialogue history record.'),
        ('D3-02C-Event-time-fallback','blocked',c,'02B plus clear one associated timestamp candidate.'),
        ('D3-05-Direct-entry','chapter4',core.SaveFile(start.edited(saves['chapter4'],5)),
         'Integrated chapter start: train, then complete the certification objective.'),
        ('D3-06-Direct-entry','chapter4',core.SaveFile(start.edited(saves['chapter4'],6)),
         'Integrated chapter start: follow the Trading Company objective through the port doors.'),
    ]
    records=[]; pending=[]
    for name,source,g,note in plans:
        f=saves[source];before=start.normalized_blocks(f);after=start.normalized_blocks(g)
        allowed={'GameUserData'} if source=='blocked' else {'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}
        changed={k for k in before if before[k]!=after[k]}
        if before.keys()!=after.keys() or changed-allowed: raise ValueError('Unexpected root edit')
        if before['UnitPool']!=after['UnitPool'] or tutorials.read(f)!=tutorials.read(g):
            raise ValueError('Party or tutorial edit')
        if source=='blocked' and story.read(f)!=story.read(g): raise ValueError('Diagnostic bypasses objective')
        fa,fb=flag_snapshot(f),flag_snapshot(g)
        changes=[{'member:hash':k,'before':fa.get(k),'after':fb.get(k)}
                 for k in sorted(fa.keys()|fb.keys()) if fa.get(k)!=fb.get(k)]
        box=container.SaveFile(str(paths[source]));box.payload=g.payload;raw=box.to_bytes()
        pending.append((name,raw,g.payload))
        records.append({'case':name,'source':source,'source_sha256':hashes[source],
                        'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
                        'note':note,'changed_roots':sorted(changed),'flag_changes':changes,
                        'party':'byte-identical','tutorials':'unchanged','game_result':'pending'})
    output.mkdir(parents=True)
    for name,raw,payload in pending:
        folder=output/name;folder.mkdir();path=folder/'Auto';path.write_bytes(raw)
        reopened=container.SaveFile(str(path));f=core.SaveFile(reopened.payload);info=start.validate(f)
        story.check_outer(reopened.raw,info)
        if reopened.verify() or reopened.payload!=payload: raise ValueError('Export roundtrip failed')
        if reopened.raw[48:57]!=payload[info.header+20:info.header+29]: raise ValueError('Clock summary mismatch')
    for name,path in paths.items():
        if path.read_bytes()!=originals[name]: raise ValueError('Source changed')
    report={'evidence':'Focused diagnostics / direct-entry regression pending','sources':hashes,'cases':records}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('returns1','returns2','test1','output'): parser.add_argument(name,type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.returns1,args.returns2,args.test1,args.output),indent=2))
