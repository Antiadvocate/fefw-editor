"""Focused Theodora city/mapping probes from exact private Test 1 returns.

No story beat is skipped. Test 2 accepted 04, 06A, 08 and 09A; the production writer now
applies their exact deltas. This historical builder retains all six probes. Private save bytes are not bundled.
"""
from pathlib import Path
from collections import deque, defaultdict
import argparse
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import facilities as fac
import story
import story_start as start
import tutorials
import worldmap
from research.dietrich_retry_kit import flag_snapshot

SOURCES = {
    4: 'b98be9d05dd52563f4e95dae567d347299934edd92dd7e373afd7dcd4ac9a12e',
    6: '088de83090cf8c7473ff3c6c0895b2030b379e3fc3dc482aa5c99cfefd845291',
    8: 'd824e3c4ec2a7e35d0ff9a379c57fdde4c9e3bb2d973aaf4c6298dadf9df80fa',
    9: 'd3f2341d76bb3ab491335c4265a8594b2caadd1470f309427d8884d6f4b24293',
}
MIDDLE, LOWER, DISTRICT = 0x16b679c4, 0x8386d712, 0xa9d310ac
FUNCTIONS = (0x948de8dd, 0x9402533e, 0xa78e9de8)
CATALOG_SHA = '0eca46855f64547ffc9d7b4efa5bcb5f2507e47db54ab3c9d1d270c6d862db3f'


def reveal_route(f, destination):
    """Research-only visibility probe; retain visited, secondary and all tails."""
    path = Path(worldmap.HERE)/'map_spots.json'
    if hashlib.sha256(path.read_bytes()).hexdigest() != CATALOG_SHA:
        raise ValueError('Map catalogue differs from the researched road graph')
    cat=worldmap.catalog();by_name={s.jp:s.index for s in cat.spots};adj=defaultdict(set)
    for road in cat.roads:
        for a,b in zip(road,road[1:]):adj[a].add(b);adj[b].add(a)
    origin=by_name['トロイアの祠'];dest=by_name[destination]
    queue=deque([(origin,[origin])]);seen={origin};route=None
    while queue:
        at,chain=queue.popleft()
        if at==dest:route=chain;break
        for child in sorted(adj[at]):
            if child not in seen:seen.add(child);queue.append((child,chain+[child]))
    expected=3 if destination=='迷いの森' else 37 if destination=='フェザーン関' else None
    if expected is None or route is None or len(route)!=expected:
        raise ValueError('Unexpected route profile')
    keys=[cat.spots[i].key for i in route];recs=worldmap.read(f)
    if any(k not in recs or not recs[k].editable or recs[k].state not in (1,2,3) for k in keys):
        raise ValueError('Unsupported route node encoding')
    g=core.SaveFile(f.payload)
    _,skipped=worldmap.apply(g,{k:(worldmap.SHOWN,None) for k in keys})
    if skipped:raise ValueError('Map repair skipped a point')
    allowed={recs[k].at+4 for k in keys}
    if len(g.payload)!=len(f.payload) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(f.payload,g.payload))):
        raise ValueError('Map repair changed bytes outside selected visibility states')
    return g


def build(returns, output):
    returns,output=Path(returns),Path(output)
    if output.exists():raise ValueError('Use a fresh output directory')
    paths={ch:returns/f'T1-{ch:02d}-Chapter-{ch:02d}'/'Auto' for ch in SOURCES}
    saves={};originals={}
    for ch,path in paths.items():
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=SOURCES[ch]:raise ValueError('Wrong source: '+str(path))
        box=container.SaveFile(str(path));f=core.SaveFile(box.payload);info=story.read(f)
        if box.verify() or (info.route,info.part,info.chapter)!=(3,1,ch):raise ValueError('Invalid source')
        if (box.raw[40:43]!=f.payload[info.header+12:info.header+15]
                or box.raw[73:81]!=f.payload[info.header+45:info.header+53]
                or box.raw[48:57]!=f.payload[info.header+20:info.header+29]):raise ValueError('Source summary mismatch')
        saves[ch]=f;originals[ch]=raw
    def city(ch,keys):return core.SaveFile(fac.edited(saves[ch],{h:True for h in keys}))
    plans=[
        ('T2-04-Middle-gate',4,city(4,(MIDDLE,)), 'Clear only middle-area movement restriction; try the arena gate.'),
        ('T2-06A-City-passages',6,city(6,(MIDDLE,LOWER,DISTRICT)), 'Clear three earlier city movement restrictions; walk to the Trading Company and progress.'),
        ('T2-06B-Passages-and-functions',6,city(6,(MIDDLE,LOWER,DISTRICT,*FUNCTIONS)), 'Only if 06A clears the paths but access/service is still missing: also enable upper/lower function access and Vandahl Trading Company.'),
        ('T2-08-City-passages',8,city(8,(MIDDLE,LOWER,DISTRICT)), 'Clear three city movement restrictions; test the blocked objective.'),
        ('T2-09A-Troy-exit',9,reveal_route(saves[9],'迷いの森'), "Show Troy's Shrine, Junction 374 and Wandering Wood; test movement and continued progression."),
        ('T2-09B-Route-to-Fezzan',9,reveal_route(saves[9],'フェザーン関'), 'Only if 09A leaves the later route unavailable: show the 37-node road path to Fezzan Gate. Does not unlock gates, clear dungeons, mark visits or bypass encounters.'),
    ]
    records=[];pending=[]
    for name,ch,g,note in plans:
        f=saves[ch];a,b=start.normalized_blocks(f),start.normalized_blocks(g)
        changed={k for k in a if a[k]!=b[k]};allowed={'GmapSpotMgr'} if ch==9 else {'GameUserData'}
        if a.keys()!=b.keys() or changed-allowed:raise ValueError('Unexpected root change')
        if tutorials.read(f)!=tutorials.read(g) or a['UnitPool']!=b['UnitPool']:raise ValueError('Party/tutorial change')
        before,after=flag_snapshot(f),flag_snapshot(g)
        flag_changes=[{'member:hash':k,'before':before.get(k),'after':after.get(k)}
                      for k in sorted(before.keys()|after.keys()) if before.get(k)!=after.get(k)]
        ma,mb=worldmap.read(f),worldmap.read(g)
        map_changes=[{'key':f'{k:08x}','name':ma[k].spot.name,'before':[ma[k].state,ma[k].secondary,ma[k].visited],
                      'after':[mb[k].state,mb[k].secondary,mb[k].visited]}
                     for k in ma if (ma[k].state,ma[k].secondary,ma[k].visited)!=(mb[k].state,mb[k].secondary,mb[k].visited)]
        if ch==9 and flag_changes or ch!=9 and map_changes:raise ValueError('Probe crossed its declared scope')
        box=container.SaveFile(str(paths[ch]));box.payload=g.payload;raw=box.to_bytes()
        pending.append((name,raw,g.payload))
        records.append({'case':name,'chapter':ch,'source_sha256':SOURCES[ch],
                        'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'note':note,
                        'changed_roots':sorted(changed),'flag_changes':flag_changes,'map_changes':map_changes,
                        'party':'byte-identical','tutorials':'unchanged','story_and_clock':'unchanged','game_result':'pending'})
    output.mkdir(parents=True)
    for name,raw,payload in pending:
        folder=output/name;folder.mkdir();path=folder/'Auto';path.write_bytes(raw)
        box=container.SaveFile(str(path));f=core.SaveFile(box.payload);info=story.read(f)
        if box.verify() or box.payload!=payload:raise ValueError('Export roundtrip failed')
        if (box.raw[40:43]!=payload[info.header+12:info.header+15]
                or box.raw[73:81]!=payload[info.header+45:info.header+53]
                or box.raw[48:57]!=payload[info.header+20:info.header+29]):raise ValueError('Export summary mismatch')
    for ch,path in paths.items():
        if path.read_bytes()!=originals[ch]:raise ValueError('Source was changed')
    result={'route':'Theodora','evidence':'Focused repairs; game tests pending','sources':SOURCES,'cases':records}
    (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('returns',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.returns,a.output),ensure_ascii=False,indent=2))
