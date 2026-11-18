"""Atomic, selected-save recruitment and guarded identity editing.

Creation uses an explicit version-36 record, never another character's state.
These edits are data-derived candidates until their game checks are reported.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import struct

import fefw_core as core
import facilities
import story

HERE = Path(__file__).resolve().parent
MIN_NUMBER, MAX_NUMBER = 1, 254  # 0 and 255 are not allocated.


@lru_cache(maxsize=1)
def catalog():
    try:
        raw = json.loads((HERE/'unit_catalog.json').read_text(encoding='utf8'))
        if raw['schema'] != 1: raise ValueError('unknown schema')
        entries = {int(k,16):v for k,v in raw['entries'].items()}
        aliases = {}
        for h,r in entries.items():
            if core.id_hash(r['pid']) != h or not r['name'] or r['level'] != 1:
                raise ValueError('invalid identity/defaults')
            if not 1 <= r['hp'] <= 999 or len(r['skills']) != 6:
                raise ValueError('invalid unit defaults')
            classes = r.get('registered_classes', [r['class']])
            if (not 1 <= len(classes) <= 255 or len(set(classes)) != len(classes)
                    or r['class'] not in classes or any(not 0 < int(c,16) <= 0xffffffff for c in classes)):
                raise ValueError('invalid registered classes')
            for a in [h, *(int(a,16) for a in r['aliases'])]:
                if a in aliases and aliases[a] != h: raise ValueError('ambiguous character alias')
                aliases[a] = h
        return entries
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise core.SaveError(f'Cannot load recruit catalogue: {exc}') from exc


@lru_cache(maxsize=1)
def identities():
    return {a:h for h,r in catalog().items() for a in [h,*(int(x,16) for x in r['aliases'])]}


def canonical(person):
    return identities().get(person, person)


def apply_labels(names):
    """Label recovered primary flags and distinguish existing alternate keys."""
    updates = {}
    try:
        legacy = json.loads((HERE/'unit_ids.json').read_text(encoding='utf8'))
    except (OSError, ValueError) as exc:
        raise core.SaveError(f'Cannot load unit labels: {exc}') from exc
    known_names = {row['name'] for row in catalog().values()}
    # Older catalogue keys based on English names are not recovered Person
    # aliases. Mark their existing labels as unverified; never merge identities
    # or synthesize new save flags from these names.
    for meta in legacy.values():
        if meta.get('src') != 'key' or meta.get('name') not in known_names:
            continue
        pid = meta.get('pid', '')
        if not pid.startswith('PID_'):
            continue
        for token, prefix in (('加入_', 'Recruited'), ('面識_', 'Met')):
            key = token + pid[4:];h = core.id_hash(key)
            if names.get(h, {}).get('name') == key:
                updates[h] = {**names[h], 'label': f"{prefix}: {meta['name']} (unverified alias)"}
    for row in catalog().values():
        for key, prefix in ((row['recruit_flag'], 'Recruited'), (row['met_flag'], 'Met')):
            if not key:
                continue
            h = core.id_hash(key)
            if names.get(h, {}).get('name', key) != key:
                raise core.SaveError(f'Conflicting unit flag identity for {h:08x}')
            updates[h] = {**names.get(h, {}), 'name': key, 'label': f"{prefix}: {row['name']}"}
    for h, meta in names.items():
        key = meta.get('name', '')
        for token, prefix in (('加入_', 'Recruited'), ('面識_', 'Met')):
            if not key.startswith(token):
                continue
            person = core.id_hash('PID_' + key[len(token):])
            main = identities().get(person)
            if main is None or main == person:
                continue
            if core.id_hash(key) != h:
                raise core.SaveError(f'Conflicting alternate unit flag identity for {h:08x}')
            updates[h] = {**meta, 'label': f"{prefix}: {catalog()[main]['name']} (alternate record)"}
    names.update(updates)


def require_context(f):
    info = story.read(f)
    if not ((info.part in (1, 2) and info.route in (1, 2, 3, 4))
            or (info.part == 3 and info.route == 9)):
        raise core.SaveError('Unit creation/renumbering supports the four Part 1/2 routes and Eshmel Part 3.')
    kind=context(f, info)
    if kind == 'mid-battle':
        raise core.SaveError('Adding or restoring units during a battle is disabled: added reserves did not become available in game. Use a pre-battle, free-time or chapter-start save.')
    if kind == 'world-map':
        raise core.SaveError('World-map battle state is not supported for Add Unit. Use a normal pre-battle, free-time or chapter-start save.')
    if kind not in ('free-time', 'pre-battle', 'chapter-start'):
        raise core.SaveError('This save context is not supported for unit creation.')
    if f.block('UnitPool') is None: raise core.SaveError('No live unit pool.')
    # Also validates the supported live flag store before touching any record.
    recruitment_map(f)
    return info


def context(f, info=None):
    info = info or story.read(f)
    mode=bytes(f.payload[info.header+20:info.header+22])
    if mode == b'\x12\x02':
        # The preparation flag distinguishes tactical setup from an active fight.
        # World-map battle mode has a different lifecycle and is not inferred here.
        return {1:'pre-battle',0:'mid-battle'}.get(f.payload[info.header+17], 'unsupported')
    return {b'\x12\x05':'free-time', b'\x12\x04':'world-map',
            b'\x10\x0b':'chapter-start'}.get(mode, 'unsupported')


def recruitment_map(f):
    # Native chapter checkpoints can precede the facility-map anchors.
    return facilities.locate_member(f, facilities.GENERAL_MEMBER)


def _unit_gear(f, u):
    """Read equipment and number forwards, including the v9 battle object.

    Battle-only history can have another version; tail-marker searches are not
    suitable for identifying its number. No battle state is written here.
    """
    p=f.payload; cur=f.ptr(u.start+72)
    if cur < u.start+76 or cur+8>u.end:
        raise core.SaveError('Unknown unit mastery layout.')
    cur+=8
    for _ in range(7):
        nxt=f.ptr(cur)
        if not cur+4<=nxt<=u.end: raise core.SaveError('Unknown unit skill layout.')
        cur=nxt
    if cur+3>=u.end or p[cur]!=35: raise core.SaveError('Unknown unit equipment version.')
    ride_at=cur+1
    if p[ride_at]==0: ride=None;cur=ride_at+1
    else:
        ride,cur=core.Ride.read(p,ride_at,u.end)
        if ride is None: raise core.SaveError('Unknown unit mount.')
    legion_at=cur;legion=None
    if p[cur]==0:cur+=1
    elif p[cur]==1 and cur+17<u.end:
        legion=core.Legion(p[cur+1],p[cur+2],struct.unpack_from('<Q',p,cur+9)[0]);cur+=17
    else:raise core.SaveError('Unknown unit battalion.')
    if p[u.start+5]==1:
        at=(cur+3)&~3
        if any(p[cur:at]) or at+5>=u.end:raise core.SaveError('Unknown battle-state alignment.')
        end=f.ptr(at)
        if not at+5<end<u.end-12 or p[at+4]!=9:
            raise core.SaveError('Unknown unit battle-state object.')
        number_at=end+1
    else:
        number_at=cur+1
    if (number_at+10>=u.end or p[number_at-1]!=0
            or p[number_at+1:number_at+3]!=b'\0\3'
            or p[number_at+9] not in (33,65)):
        raise core.SaveError('Unknown unit identity layout.')
    return core.Gear(p[number_at],ride_at,legion_at-ride_at,ride,
                     legion_at,cur-legion_at,legion)


def _pool_groups(f):
    """Decode counted player, reserve and opponent lists without merging them."""
    pool=f.block('UnitPool')
    if pool is None or f.payload[pool.start+4]!=0:
        raise core.SaveError('Unrecognised live unit pool.')
    tree=f.tree();at=pool.start+5;groups=[];seen=set()
    while at<pool.end:
        kind=f.payload[at]
        if kind==255:
            if bytes(f.payload[at:pool.end])!=b'\xff'+bytes(pool.end-at-1) or pool.end-at>4:
                raise core.SaveError('Unexpected data after the live unit pool.')
            return groups
        if kind not in (0,1,3,4,6,7) or kind in seen or at+3>pool.end:
            raise core.SaveError('Unknown or duplicate unit-pool group.')
        seen.add(kind);count=f.u16(at+1);start=(at+6)&~3
        if any(f.payload[at+3:start]):raise core.SaveError('Unknown unit-pool padding.')
        cursor=start;rows=[]
        for _ in range(count):
            if cursor+84>pool.end:raise core.SaveError('Truncated live unit pool.')
            end=f.ptr(cursor)
            if (not cursor+84<=end<=pool.end or end%4 or tree.node_at(cursor)<0
                    or f.payload[cursor+4]!=36 or f.payload[cursor+5] not in (0,1)):
                raise core.SaveError('Unknown or incomplete unit record.')
            u=core.SaveUnit.read(f,cursor);rows.append((u,_unit_gear(f,u)));cursor=end
        groups.append((kind,at,cursor,rows));at=cursor
    raise core.SaveError('Missing live unit-pool terminator.')


def pool_groups(f):
    try:
        return _pool_groups(f)
    except (IndexError, struct.error) as exc:
        raise core.SaveError('Truncated or malformed unit-pool records; nothing changed.') from exc


def roster(f):
    """All player records, including reserves and story-hidden units.

    Opponents may legitimately share an identity (including a protagonist).
    Their numbers are reserved separately during allocation.
    """
    return [row for kind,_,_,rows in pool_groups(f) if kind in (0,4,6,7) for row in rows]


def flag_values(f):
    return {x.hash:x.value for x in recruitment_map(f).flags}


def status(f, person, rows=None, values=None):
    row = catalog()[person]
    hits = [(u,g) for u,g in (roster(f) if rows is None else rows) if canonical(u.person)==person]
    if hits:
        if len(hits)>1: return 'Duplicate character records — review required'
        if hits[0][0].person != person: return 'Alternate record exists — review required'
        recruited = (flag_values(f) if values is None else values).get(core.id_hash(row['recruit_flag']))
        if recruited == 1: return 'Already in party'
        if recruited in (None,0) and hits[0][0].flags == 0:
            return 'Existing inactive record — restore recruitment'
        return 'Existing record — recruitment state needs review'
    return row['restriction'] or 'Not present — add level 1'


def _equipment_records(f):
    """Typed reference fields only: no raw-byte search/replace."""
    result=[]; seen=set()
    party=core.party_store(f)
    if party is None:
        raise core.SaveError('The party equipment stores could not be identified.')
    for st in (party, core.reliquary_store(f)):
        if not st: continue
        for kind,at in (('ride',st[1]),('legion',st[2])):
            if at in seen: continue
            seen.add(at)
            end=f.ptr(at)
            if end<at+7 or end>len(f.payload) or f.payload[at+4]!=0:
                raise core.SaveError('Unknown equipment pool header.')
            count=f.u16(at+5); pos=at+7
            for _ in range(count):
                if pos >= end: raise core.SaveError('Truncated equipment pool.')
                if f.payload[pos] == 0: pos+=1;continue
                if kind=='ride':
                    obj,nxt=core.Ride.read(f.payload,pos,end)
                    if obj is None: raise core.SaveError('Unknown mount record.')
                    result.append((pos+9,obj.owner,obj.allies));pos=nxt
                else:
                    if f.payload[pos]!=1 or pos+17>end: raise core.SaveError('Unknown battalion record.')
                    result.append((pos+2,f.payload[pos+2],b''));pos+=17
            if end-pos>3 or any(f.payload[pos:end]):
                raise core.SaveError('Unexpected trailing equipment data.')
    return result


def _references(f, rows):
    refs = _equipment_records(f)
    for u,g in rows:
        if g.ride: refs.append((g.ride_at+9,g.ride.owner,g.ride.allies))
        if g.legion: refs.append((g.legion_at+2,g.legion.owner,b''))
    return refs


def next_number(f):
    rows=roster(f)
    people=[canonical(u.person) for u,_ in rows]
    if len(people)!=len(set(people)): raise core.SaveError('Existing duplicate character records must be reviewed first.')
    all_rows=[row for _,_,_,group in pool_groups(f) for row in group]
    nums=[g.unit_number for _,g in all_rows]
    if len(nums)!=len(set(nums)): raise core.SaveError('Existing duplicate unit numbers must be repaired first.')
    refs=_references(f,all_rows)
    if any(allies for _,_,allies in refs):
        raise core.SaveError('Mount affinity references are not yet mapped; allocating a new identity is disabled.')
    used=set(nums)|{owner for _,owner,_ in refs if owner not in (0,255)}
    # Do not recycle holes: other records may retain a historical identity.
    number=max(used,default=0)+1
    if not MIN_NUMBER<=number<=MAX_NUMBER: raise core.SaveError('No supported unused unit number remains.')
    return number


def _recruit(f,row):
    work=f.copy()
    for name in (row['recruit_flag'],row['met_flag']):
        if not name: continue
        fm=recruitment_map(work);h=core.id_hash(name)
        matches=[x for x in fm.flags if x.hash==h]
        if len(matches)>1 or (matches and (matches[0].wide or matches[0].value not in (0,1))):
            raise core.SaveError('Unknown recruitment/met state; unchanged.')
        if matches:
            work.payload[matches[0].offset]=1
        else:
            work=core.SaveFile(core.flag_add(work,fm,h,1))
    return work


def _record(row,number,at):
    """Construct the observed record format from typed fields and empty history."""
    b=bytearray(72);b[4]=36
    struct.pack_into('<II',b,10,core.id_hash(row['pid']),int(row['class'],16))
    # Independent positive 31-bit seed words, within the observed native range.
    # Their initialization is inferred and still needs game level-up checks.
    seed=hashlib.sha256(f"{row['pid']}:{number}".encode()).digest()[:8]
    struct.pack_into('<II',b,18,*(max(1,x & 0x7fffffff) for x in struct.unpack('<II',seed)))
    b[59]=1;struct.pack_into('<H',b,64,row['hp'])
    def leaf(body):
        start=len(b);b.extend(bytes(4)+body);b.extend(bytes(-len(b)%4))
        struct.pack_into('<I',b,start,at+len(b)+32)
    mastery=bytes([len(row['masteries'])])+b''.join(struct.pack('<BH',i,v) for i,v in row['masteries'])
    classes = row.get('registered_classes', [row['class']])
    leaf(mastery+bytes([len(classes)])+b''.join(struct.pack('<IBB',int(c,16),0,4) for c in classes))
    b.extend(b'\xff\xff\xff\xff\0\0\0\0')
    inventory=row['items']+row['magic']
    leaf(bytes([0,len(row['items']),len(row['magic'])])+b''.join(b'\x41'+struct.pack('<I',int(h,16)) for h in inventory))
    for skills in row['skills']:
        leaf(b'\0'+struct.pack('<H',len(skills))+b''.join(b'\x43'+struct.pack('<I',int(h,16)) for h in skills))
    # Version 35 equipment, no mount/battalion, number, empty version 33 history.
    b.extend(bytes([35,0,0,0,number,0,3,0,0,0,0,0,0,33,0,0,4,0,5,0]))
    b.extend(b'\0\0\0\0\0\xff\xff\0');b.extend(bytes(-len(b)%4))
    struct.pack_into('<I',b,0,at+len(b)+32)
    return bytes(b)


def add(f,person):
    require_context(f)
    if person not in catalog(): raise core.SaveError('Choose a catalogued recruit.')
    row=catalog()[person]
    if row['restriction']: raise core.SaveError(row['restriction'])
    existing=[u for u,_ in roster(f) if canonical(u.person)==person]
    if existing: raise core.SaveError(status(f,person)+'. A second copy will not be added.')
    number=next_number(f)
    # Validate flags before constructing an appended record, preserving every old unit.
    work=_recruit(f,row);pool=work.block('UnitPool');tree=work.tree()
    groups=pool_groups(work);party=next((g for g in groups if g[0]==4),None)
    if party is None:
        # During tactical preparation, create the unfielded party list.
        if context(work)!='pre-battle':raise core.SaveError('No supported party group.')
        at=next((g[1] for g in groups if g[0]>4),pool.end-4)
        body=b'\4\1\0\0'+_record(row,number,at+4)
    else:
        _,header,at,oldrows=party;body=_record(row,number,at)
    new=tree.splice(tree.node_at(pool.start),at,0,body)
    if party is not None:struct.pack_into('<H',new,header+1,len(oldrows)+1)
    result=core.SaveFile(new);rows=roster(result)
    old_ids=[(u.person,g.unit_number) for u,g in roster(work)]
    if [(u.person,g.unit_number) for u,g in rows if u.person!=person] != old_ids:
        raise core.SaveError('Existing unit identities changed; nothing applied.')
    if [(u.person,g.unit_number) for u,g in rows if u.person==person] != [(person,number)]:
        raise core.SaveError('New unit did not read back.')
    return new


def restore(f,person):
    require_context(f)
    if status(f,person) != 'Existing inactive record — restore recruitment':
        raise core.SaveError('This record cannot be restored through the recruit action.')
    rows=roster(f)
    people=[canonical(u.person) for u,_ in rows]
    if len(people)!=len(set(people)): raise core.SaveError('Existing duplicate character records must be reviewed first.')
    nums=[g.unit_number for _,g in rows]
    if len(nums)!=len(set(nums)): raise core.SaveError('Existing duplicate unit numbers must be repaired first.')
    return _recruit(f,catalog()[person]).payload


def renumber(f,person,number):
    require_context(f)
    if (context(f) != 'free-time' or [g[0] for g in pool_groups(f)] != [4]
            or any(f.payload[u.start+4:u.start+8] != b'\x24\0\0\0' for u,_ in roster(f))):
        raise core.SaveError('Renumbering requires a free-time party save; battle references are not rewritten.')
    if type(number) is not int or not MIN_NUMBER<=number<=MAX_NUMBER:
        raise core.SaveError('Unit number must be an integer from 1 to 254.')
    rows=roster(f);hits=[(u,g) for u,g in rows if u.person==person]
    if len(hits)!=1: raise core.SaveError('No unique live character record.')
    u,g=hits[0];old=g.unit_number
    if number==old:return bytearray(f.payload)
    if sum(canonical(v.person)==canonical(person) for v,_ in rows)>1:
        raise core.SaveError('This character has multiple live records; review them before renumbering.')
    if any(x.unit_number==number for _,x in rows): raise core.SaveError('That unit number is already used by another live unit.')
    refs=_references(f,rows)
    if any(allies for _,_,allies in refs):
        raise core.SaveError('Mount affinity references are not yet mapped; renumbering this save is disabled.')
    if any(owner==number for _,owner,_ in refs): raise core.SaveError('That number is still referenced by equipment.')
    if sum(x.unit_number==old for _,x in rows)>1 and any(owner==old for _,owner,_ in refs):
        raise core.SaveError('Duplicate number has ambiguous equipment ownership; cannot renumber safely.')
    out=bytearray(f.payload);tail=core.tail_at(out,u.start,u.end);out[tail-9]=number
    for at,owner,_ in refs:
        if owner==old:out[at]=number
    checked=roster(core.SaveFile(out))
    if next(x.unit_number for v,x in checked if v.person==person)!=number:
        raise core.SaveError('Renumber did not read back.')
    return out


def copy_in(src,unit,dst):
    """Guard the existing import path against character and number collisions."""
    require_context(dst)
    if context(dst) != 'free-time' or len(pool_groups(dst)) != 1:
        raise core.SaveError('Copy unit in requires a free-time save with one party group.')
    if any(canonical(u.person)==canonical(unit.person) for u,_ in roster(dst)):
        raise core.SaveError('This character already has a live record in the destination.')
    number=next_number(dst)
    gear=core.gear(src,unit)
    if gear is None: raise core.SaveError('Source identity/equipment layout is unknown.')
    if gear.ride or gear.legion:
        raise core.SaveError('Detach the source mount/battalion before importing; shared equipment is not copied.')
    work=core.SaveFile(core.copy_unit(src,unit,dst));u=work.units()[-1]
    tail=core.tail_at(work.payload,u.start,u.end);work.payload[tail-9]=number
    roster(work)
    return work.payload
