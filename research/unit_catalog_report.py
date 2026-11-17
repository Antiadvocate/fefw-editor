"""Reproduce level-one recruit metadata from private game tables, never saves.

Run with GameData and --output unit_catalog.json. No localized message bodies,
game binaries or personal unit records are copied into the catalogue.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fefw_core as core
from fefw_save import SKILL_THRESHOLDS
from research import facility_access_report as tables

HERE = Path(__file__).resolve().parents[1]


def records(data):
    schema = data.schemas[0]
    out = {}
    for at in range(schema['end'], len(data.b)-schema['stride'], schema['stride']):
        key = data.string(data.q(at+8))
        if not key or key in out:
            break
        out[key] = at
    return out


def array(data, at):
    count, stride = struct.unpack_from('<HH', data.b, at)
    pointer = data.q(at+8)+32
    if stride != 16 or count > 255 or (count and pointer+count*stride > len(data.b)):
        raise ValueError('Unrecognised data array')
    result = [data.string(data.q(pointer+i*stride)) for i in range(count)]
    if not all(result): raise ValueError('Missing array identity')
    return result


def report(directory, *, extra_profiles=None, accepted_defaults=True):
    # Research-only explicit overrides; the normal catalogue remains identical.
    # Passing these does not enable any candidate in the editor.
    extra_profiles = extra_profiles or {}
    tables.BASE = Path(directory)
    person = tables.Data('Person.bin'); jobs = tables.Data('Job.bin')
    growth = tables.Data('Growth.bin'); skills = tables.Data('Skill.bin')
    prows, jrows, srows = records(person), records(jobs), records(skills)
    for key, profile in extra_profiles.items():
        if key not in prows or set(profile) - {'class_key', 'hp', 'ranks'}:
            raise ValueError('Unknown experimental identity or override')
    names = json.loads((HERE/'unit_ids.json').read_text())
    flags = {r['name'] for r in json.loads((HERE/'flag_names.json').read_text()).values()}
    items = json.loads((HERE/'item_ids.json').read_text())
    skill_ids = json.loads((HERE/'skill_ids.json').read_text())
    canonical = {key:at for key,at in prows.items()
                 if (0 < person.b[at+48] < 100 and '加入_'+key[4:] in flags)
                 or key in extra_profiles}
    short_ids = {person.string(person.q(at+40)): key for key,at in canonical.items()}
    entries = {}
    for key,at in canonical.items():
        h = f'{core.id_hash(key):08x}'
        profile = extra_profiles.get(key, {})
        job = profile.get('class_key', person.string(person.q(at+56)))
        ranks = profile.get('ranks', list(person.b[at+584:at+597]))
        if len(ranks) != 13 or any(type(x) is not int or x < 0 for x in ranks):
            raise ValueError('Invalid experimental ranks')
        if any(x > len(SKILL_THRESHOLDS) for x in ranks): raise ValueError('Unknown rank')
        masteries = [[i, SKILL_THRESHOLDS[rank-1]] for i,rank in enumerate(ranks) if rank]
        learned = []
        for lid in array(person, at+136):
            group = growth.refs_to_string(lid)[0]-8
            count = struct.unpack_from('<H',growth.b,group+18)[0]
            ptr = growth.q(group+32)+32
            for i in range(count):
                row = ptr+i*72
                if growth.string(growth.q(row+8)) != lid: raise ValueError('Bad learn row')
                level, mastery, rank = growth.b[row+32:row+35]
                conditions = struct.unpack_from('<H',growth.b,row+56)[0]
                # Zero level AND zero mastery requirement denotes a scripted
                # grant, not a free starting ability (e.g. later spellsongs).
                if (not conditions and (level == 1 or rank > 0) and level <= 1
                        and (rank == 0 or (mastery < 13 and ranks[mastery] >= rank))):
                    sid = growth.string(growth.q(row+40))
                    if sid not in srows or f'{core.id_hash(sid):08x}' not in skill_ids:
                        raise ValueError('Uncatalogued starting skill '+sid)
                    if sid not in learned: learned.append(sid)
        arts = [s for s in learned if skills.b[srows[s]+104] == 2]
        passive = [s for s in learned if skills.b[srows[s]+104] == 1]
        inventory = array(person, at+120)
        magic = []
        for sid in learned:
            # Only a recovered item key is admitted, never an invented item hash.
            iid = 'IID_'+sid[4:]
            if skills.b[srows[sid]+250] == 20 and f'{core.id_hash(iid):08x}' in items:
                magic.append(iid)
        if any(f'{core.id_hash(i):08x}' not in items for i in inventory):
            raise ValueError('Uncatalogued starting item')
        aliases = [k for k,a in prows.items() if k != key and
                   (person.string(person.q(a+688)) == key or
                    (person.string(person.q(a+40)) and
                     short_ids.get(person.string(person.q(a+40))) == key))]
        name = names[h]['name']
        if job not in jrows: raise ValueError('Missing starting class')
        entries[h] = {
            'pid':key, 'name':name, 'aliases':[f'{core.id_hash(k):08x}' for k in aliases],
            'source_offset':hex(at), 'person_serial':person.b[at+48],
            'source_flags':person.b[at+49],
            'class':f'{core.id_hash(job):08x}', 'class_key':job, 'level':1,
            'hp':profile.get('hp', struct.unpack_from('<h',person.b,at+450)[0]),
            'masteries':masteries, 'items':[f'{core.id_hash(k):08x}' for k in inventory],
            'magic':[f'{core.id_hash(k):08x}' for k in magic],
            'skills':[[f'{core.id_hash(s):08x}' for s in group] for group in
                      (arts[:4], passive[:5], [], arts, [], learned)],
            'recruit_flag':'加入_'+key[4:],
            'met_flag': '面識_'+key[4:] if '面識_'+key[4:] in flags else None,
            'default_mount':person.string(person.q(at+104)),
            'evidence':'Data-derived; game test pending',
            'restriction':('Custom protagonist creation is not supported.' if key=='PID_イシュマール' else
                           'Special-character defaults need validation.' if person.b[at+49]!=39 else ''),
            'route_scope':'Route/part eligibility unverified; this is not a natural recruitment event.'}
        if key in extra_profiles:
            entries[h]['evidence'] = 'Experimental profile; game test pending'
            entries[h]['restriction'] = 'Research-only candidate; not enabled in the editor.'
            entries[h]['experimental_overrides'] = profile
    if accepted_defaults and 'PID_アンナ' not in extra_profiles:
        # A1 game acceptance, 17 November 2026: reproduce the tested input,
        # including its original class registration and carried Bronze Spear.
        anna = entries[f'{core.id_hash("PID_アンナ"):08x}']
        mounted = anna['class']
        dismounted = 'JID_戦象兵下馬'
        weapon = 'IID_青銅の槍'
        if dismounted not in jrows or f'{core.id_hash(weapon):08x}' not in items:
            raise ValueError('Missing accepted Anna defaults')
        anna.update(class_key=dismounted, **{'class': f'{core.id_hash(dismounted):08x}'})
        anna['registered_classes'] = [mounted, anna['class']]
        anna['items'] = [f'{core.id_hash(weapon):08x}']
        anna['restriction'] = ''
        anna['evidence'] = ('Dismounted-only: passed Leda Chapter 9 deployment/control tests. '
                            'Cannot remount; mounted Elephant Rider could not deploy in that battle')
    return {'schema':1, 'scope':'Level-one defaults, not chapter-scaled natural recruits. No story rewards, conditional skills or shared mounts are granted.',
            'sources':{n:hashlib.sha256((Path(directory)/n).read_bytes()).hexdigest()
                       for n in ('Person.bin','Growth.bin','Job.bin','Skill.bin')},
            'entries':entries}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('gamedata');p.add_argument('--output',type=Path)
    args=p.parse_args();data=report(args.gamedata);text=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    if args.output:args.output.write_text(text)
    else:print(text)
