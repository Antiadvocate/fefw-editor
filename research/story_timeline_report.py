"""Read a private Part 1 route timeline to verify its chapter title rows.

Chapter existence is not proof of the inferred save sequence mapping. This
report is read-only and the game dump is neither bundled nor needed at runtime.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research import facility_access_report as data


def report(gamedata, route='leda'):
    routes = {'leda': ('Led', 'レダ篇', 'LED'), 'cai': ('Kai', 'カイ篇', 'KAI'),
              'dietrich': ('Dit', 'ディートリヒ篇', 'DIT'), 'theodora': ('Seo', 'セオドラ篇', 'SEO')}
    if route not in routes:raise ValueError('Choose leda, cai, dietrich or theodora')
    suffix, group, title = routes[route]
    filename = f'Timeline_Part1_{suffix}.bin'
    data.BASE=Path(gamedata);d=data.Data(filename)
    schemas=[s for s in d.schemas if any(n=='ハッシュキー' for n,t,z,o in s['fields'])]
    if len(schemas)!=1:raise ValueError('Expected one timeline schema')
    schema=schemas[0];entries=[]
    # Group references occur in both the array header and its row headers.
    # Require the title action and one exact title ID to exclude the container.
    for ref in d.refs_to_string(group):
        at=ref-8
        if at<schema['end'] or at+schema['stride']>len(d.b):continue
        values={n:v for n,t,o,v in d.values(at,schema)}
        args=values['引数']
        if values['種類']!=10 or not isinstance(args,list) or len(args)!=1:continue
        match=re.fullmatch(r'MCID_1_'+title+r'_title(\d\d)',args[0])
        if not match:continue
        chapter=int(match[1]);stored=values['章']
        if stored!=(0 if chapter==1 else chapter):raise ValueError('Unexpected title/chapter pairing')
        previous_at=at-schema['stride']
        previous={n:v for n,t,o,v in d.values(previous_at,schema)}
        entries.append({'chapter':chapter,'title_id':args[0],'offset':hex(at),
                        'stored_chapter':stored,'year':values['年'],'month':values['月'],'day':values['日'],'time':values['時刻'],
                        'preceding_row':{'offset':hex(previous_at),'kind':previous['種類'],
                                         'args':previous['引数'],'meaning':'Unrecovered; not proof of checkpoint creation'}})
    entries.sort(key=lambda r:r['chapter'])
    if [r['chapter'] for r in entries]!=list(range(1,13)):raise ValueError('Expected exactly chapters 1–12')
    return {'source':filename,'route':route,'sha256':hashlib.sha256(d.b).hexdigest(),
            'scope':'Title-row existence and dates only; not proof of save sequence mappings or game behavior','chapters':entries}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('gamedata',type=Path)
    p.add_argument('--route',choices=('leda','cai','dietrich','theodora'),default='leda')
    a=p.parse_args();print(json.dumps(report(a.gamedata,a.route),indent=2))
