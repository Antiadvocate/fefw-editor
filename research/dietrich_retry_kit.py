"""Build isolated Dietrich Test 2 probes; never used by the story editor.

Requires the exact private Test 1 returns and delivered Test 1 kit. All repairs
are hypotheses pending game tests. No save bytes are included in this source.
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
import story_start
import tutorials

HISTORY = facilities.HISTORY_MEMBER
PROGRESSION = 0x4ad575a2
UPPER = '行動範囲制限_上層'
LOWER = '行動範囲制限_下層'
RESCUE = 'MID_EV12_002_m01'
SECRET = '使用許可_秘伝・風切投槍'
SOURCES = {
    'D1-02-Chapter-02/Auto': '56a871a45bd634f3f9d023713ee5e8c8b536db71774c0d1d4f75e38164764bed',
    'D1-05-Chapter-05/Auto-after-progress': 'b3f823c117c19f9012fcb88662ef42e7bbcacf394b5b5aa5a0bb0737d9f4abcd',
    'D1-06-Chapter-06/Auto': 'fb5f307830eb858aba690fbd3ae11f7315906571162c7fdf8e59a3f4fd3046a9',
    'D1-06-Chapter-06/Auto-after-editing': '49d3dae25d25378a86af0e00061e3c42c83a286ae687d61b80d4115258c0ceaf',
}
CH7_SHA = '278f8bd9504675ec19e52348dfdd2f42e81345942917960ae7eb307194150f24'


def member_map(f, member):
    tree, group, _ = facilities.flag_group(f)
    node = tree.nodes[group]; table = f.ptr(node.start)
    rows = [(f.u32(table+8*i), f.ptr(table+8*i+4)) for i in range(f.u32(node.start)>>24)]
    starts = [at for key,at in rows if key == member]
    if len(starts) != 1:
        raise core.SaveError('Missing or ambiguous research flag member')
    hits = [m for m in core.flag_maps(f) if m.start == starts[0]]
    if len(hits) != 1 or len({v.hash for v in hits[0].flags}) != len(hits[0].flags):
        raise core.SaveError('Missing, empty or ambiguous research flag list')
    if tree.nodes[tree.node_at(starts[0])].parent != group:
        raise core.SaveError('Research flag list is outside its expected group')
    return hits[0]


def flag_edit(f, member, key, value):
    if member not in (HISTORY, PROGRESSION) or value not in (None, 1):
        raise core.SaveError('Unsupported research edit')
    fm = member_map(f, member); h = core.id_hash(key)
    old = [v for v in fm.flags if v.hash == h]
    if old and (old[0].value != 1 or old[0].wide):
        raise core.SaveError('Unexpected source flag encoding')
    if value is None:
        if len(old) != 1: raise core.SaveError('Expected source flag is absent')
        p = core.flag_remove(f, fm, old[0])
    elif old:
        p = bytearray(f.payload)
    else:
        p = core.flag_add(f, fm, h, 1)
    return core.SaveFile(p)


def reset_two_hub_lists(f):
    """Broader fallback: two cached state lists, not claimed as decoded events.

    Only called for fingerprinted C2 return. Keep every other HubData field.
    The list identities are not established sufficiently for production use.
    """
    tree=core.SaveTree(f.payload); block=f.block('HubData'); idx=tree.node_at(block.start)
    children=[n for n in tree.nodes if n.parent==idx]
    if len(children)!=10 or f.payload[block.start+4]!=21:
        raise core.SaveError('Unknown HubData research layout')
    plans=[]
    for pos,count in ((6,2),(7,37)):
        node=children[pos]
        if (f.payload[node.start+4]!=0 or f.u16(node.start+5)!=count
                or node.end-node.start!=8+20*count):
            raise core.SaveError('HubData research list does not match capture')
        subs=[n for n in tree.nodes if n.parent==tree.node_at(node.start)]
        if len(subs)!=count or any(n.end-n.start!=20 or f.payload[n.start+4]!=0 for n in subs):
            raise core.SaveError('Unexpected HubData list records')
        plans.append(node.start)
    for at in sorted(plans,reverse=True):
        tree=core.SaveTree(f.payload);idx=tree.node_at(at);node=tree.nodes[idx]
        f=core.SaveFile(tree.splice(idx,at+4,node.end-at-4,bytes(4)))
    return f


def soldier_esmeralda(f):
    units=[u for u in f.units() if u.person==core.id_hash('PID_エスメラルダ')]
    if len(units)!=1:raise core.SaveError('Expected one Esmeralda')
    u=units[0];cid=core.id_hash('JID_兵士')
    classes=list(u.classes)
    if not any(row[0]==cid for row in classes):classes.append((cid,0,0))
    f=core.SaveFile(core.with_lists(f,u,u.masteries,classes))
    u=next(u for u in f.units() if u.person==core.id_hash('PID_エスメラルダ'))
    core.set_class(f,u,cid)
    return f


def flag_snapshot(f):
    tree,group,_=facilities.flag_group(f);node=tree.nodes[group];tab=f.ptr(node.start)
    lookup={f.ptr(tab+8*i+4):f.u32(tab+8*i) for i in range(f.u32(node.start)>>24)}
    return {f'{lookup[m.start]:08x}:{v.hash:08x}': [v.value,v.wide]
            for m in core.flag_maps(f) if m.start in lookup for v in m.flags}


def build(returns, test1, output):
    returns,test1,output=map(Path,(returns,test1,output))
    if output.exists():raise ValueError('Use a fresh output directory')
    paths={name:returns/name for name in SOURCES}
    paths['chapter7']=test1/'test-saves/D1-07-Chapter-07/Auto'
    hashes={**SOURCES,'chapter7':CH7_SHA};originals={};saves={}
    for name,p in paths.items():
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=hashes[name]:raise ValueError('Wrong source: '+name)
        box=container.SaveFile(str(p));f=core.SaveFile(box.payload)
        if box.verify() or story_start.validate(f).route!=2:raise ValueError('Invalid source: '+name)
        originals[name]=raw;saves[name]=f
    plans=[]
    def add(name,source,f,note,allowed):plans.append((name,source,f,note,set(allowed)))
    source='D1-02-Chapter-02/Auto';f=flag_edit(saves[source],HISTORY,RESCUE,None)
    add('D2-02A-Rescue-history',source,f,'Remove only the recorded rescue scene; approach Esmerelda again.',{'GameUserData'})
    add('D2-02B-Hub-cache-fallback',source,reset_two_hub_lists(f),
        '02A plus reset two HubData state lists (2 and 37 records). Broader research fallback, not a production fix.',{'GameUserData','HubData'})
    source='D1-05-Chapter-05/Auto-after-progress';f=flag_edit(saves[source],PROGRESSION,UPPER,None)
    add('D2-05A-Upper-restriction',source,f,'Remove only the upper-area movement restriction; resume after training.',{'GameUserData'})
    g=core.SaveFile(facilities.edited(f,{core.id_hash(k):True for k in ('機能開放_資格試験','機能開放_ダグシオン上層')}))
    add('D2-05B-Exam-switch-fallback',source,g,'05A plus Certification exams and upper-area function unlocks.',{'GameUserData'})
    source='D1-06-Chapter-06/Auto-after-editing';f=flag_edit(saves[source],PROGRESSION,LOWER,None)
    add('D2-06A-Port-restriction',source,f,'Keep the player edits; remove only the lower-area movement restriction. Keep the Chapter 6 upper restriction.',{'GameUserData'})
    source='D1-06-Chapter-06/Auto';f=flag_edit(saves[source],PROGRESSION,LOWER,None)
    add('D2-06B-Restriction-only-control',source,f,'Optional after 06A passes: remove lower restriction from the original arrival, without added function unlocks.',{'GameUserData'})
    source='chapter7';f=flag_edit(saves[source],PROGRESSION,SECRET,1)
    add('D2-07A-One-secret-permission',source,f,'Grant only Hidden Windpierce permission; test teaching Esmerelda. Costs 50 in the supplied table; the tutorial displayed 50 shards.',{'GameUserData'})
    add('D2-07B-Soldier-fallback',source,soldier_esmeralda(f),
        '07A plus set Esmerelda to Soldier (a spear class), adding that class at zero EXP. No unit, level, mastery, skill or item is added.',{'GameUserData','UnitPool'})
    output.mkdir(parents=True);records=[]
    for name,source,g,note,allowed in plans:
        f=saves[source];before=story_start.normalized_blocks(f);after=story_start.normalized_blocks(g)
        changed={k for k in before if before[k]!=after[k]}
        if before.keys()!=after.keys() or changed-allowed:raise ValueError('Unexpected root edit: '+name)
        if tutorials.read(f)!=tutorials.read(g):raise ValueError('Tutorial edit: '+name)
        if [(u.person,core.gear(f,u).unit_number) for u in f.units()]!=[(u.person,core.gear(g,u).unit_number) for u in g.units()]:
            raise ValueError('Roster edit: '+name)
        if story.read(f).sequence!=story.read(g).sequence:raise ValueError('Story bypass: '+name)
        box=container.SaveFile(str(paths[source]));box.payload=g.payload;raw=box.to_bytes()
        folder=output/name;folder.mkdir();dest=folder/'Auto';dest.write_bytes(raw)
        reopened=container.SaveFile(str(dest));h=core.SaveFile(reopened.payload);info=story_start.validate(h)
        if reopened.verify() or h.payload!=g.payload:raise ValueError('Failed export: '+name)
        if reopened.raw[40:43]!=g.payload[info.header+12:info.header+15] or reopened.raw[73:81]!=g.payload[info.header+45:info.header+53]:
            raise ValueError('Export summary mismatch')
        a,b=flag_snapshot(f),flag_snapshot(g)
        changes=[{'member:hash':k,'before':a.get(k),'after':b.get(k)} for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)]
        records.append({'case':name,'source':source,'source_sha256':hashes[source],'sha256':hashlib.sha256(raw).hexdigest(),
                        'bytes':len(raw),'chapter':info.chapter,'note':note,'changed_roots':sorted(changed),'flag_changes':changes,
                        'checksums':'pass','summary':'pass','tutorials':'unchanged','roster':'unchanged','game_result':'pending'})
    # Native checkpoint is an independent control, not an attempted repair.
    control=test1/'test-saves/00-Native-Control/Chapter_Dit_1_2';raw=control.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='c124def0b52827dac594b127c8450eca0ddd310ccd1594a332339bbc711e6d0b':
        raise ValueError('Wrong native Chapter 2 control')
    folder=output/'D2-02C-Native-control';folder.mkdir();(folder/'Auto').write_bytes(raw)
    for name,p in paths.items():
        if p.read_bytes()!=originals[name]:raise ValueError('Source was modified')
    result={'evidence':'Experimental probes; game tests pending','cases':records,
            'native_control':{'case':folder.name,'sha256':hashlib.sha256(raw).hexdigest(),'note':'Unmodified native Chapter 2 checkpoint, copied as Auto. Different native party/progress.'}}
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('returns','test1','output'):p.add_argument(name,type=Path)
    a=p.parse_args();result=build(a.returns,a.test1,a.output)
    print(f'Validated {len(result["cases"])} isolated probes and one native control.')
