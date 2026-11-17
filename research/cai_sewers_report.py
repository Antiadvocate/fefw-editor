"""Extract the exact Sewers entrance prerequisite from a private GameData dump."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research import facility_access_report as data


def report(gamedata):
    data.BASE=Path(gamedata);d=data.Data('HubDispos/Hub_000.bin');hits=[]
    for ref in d.refs_to_string('A60へ'):
        at=ref-32
        if at<0 or d.string(d.q(at+8))!='イベント_A1':continue
        schema=max((s for s in d.schemas if s['end']<=at),key=lambda s:s['at'])
        fields={o:v for n,t,o,v in d.values(at,schema)}
        if fields.get(40)!='MID_Access_Goto_Sewar':continue
        if (fields.get(80),fields.get(88),fields.get(104),fields.get(112))!=(
                '主人公',['KAI'],'既読済',['MID_LGV_1KAI_c02_LG11_003_m06']):
            raise ValueError('Unexpected entrance prerequisites')
        if fields.get(128)!='フラグORチェック' or '拠点_カイ篇1部4章_行動制限1' not in fields.get(136,[]):
            raise ValueError('Chapter 4 phase absent from entrance conditions')
        hits.append({'offset':hex(at),'group':'イベント_A1','label':fields[32],
                     'name':fields[40],'route':fields[88],'read_check':fields[104],
                     'dialogue':fields[112][0],'allowed_phase_flags':fields[136]})
    if len(hits)!=1:raise ValueError('Expected exactly one city-to-Sewers entrance')
    hub=data.Data('Hub.bin');aliases=[]
    for ref in hub.refs_to_string('既読済'):
        at=ref-40
        if at>=0 and hub.string(hub.q(at+8))=='配置条件':
            aliases.append(hub.string(hub.q(at+32)))
    if aliases!=['IsAlreadyRead']:raise ValueError('Unexpected already-read alias')
    return {'source':'HubDispos/Hub_000.bin','sha256':hashlib.sha256(d.b).hexdigest(),
            'alias_source':'Hub.bin','alias_sha256':hashlib.sha256(hub.b).hexdigest(),
            'read_function':aliases[0],'entrance':hits[0],
            'scope':'Data conditions verified; save-history mapping and game access require testing'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('gamedata',type=Path)
    print(json.dumps(report(p.parse_args().gamedata),ensure_ascii=False,indent=2))
