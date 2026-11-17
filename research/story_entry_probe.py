"""Test 2: isolate checkpoint entry, restart cache and date initialization.

Research-only, not enabled in the editor. Uses no private data at runtime.
The CLI requires the accepted private baseline and refuses existing outputs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import story

BASELINE_SHA256='8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663'
from story_start import (RESTART_KEYS, HEADER_KEY, DATA_KEY, one_block, members,
                         restart_leaves, clear_restart, normalized_blocks)
# Historical Test 2 targets and profiles, retained for reproduction.
ENTRY_DATES={4:(3,1,8),9:(7,10,18)}
CASES=(('ST2-09A-Entry-mode',9,'A'),('ST2-09B-Empty-restart',9,'B'),
       ('ST2-09C-Entry-date',9,'C'),('ST2-04C-Entry-date',4,'C'))


def edited_profile(f,chapter,profile):
    if (type(chapter) is not int or chapter not in ENTRY_DATES or profile not in ('A','B','C')):
        raise core.SaveError('Only the Chapter 4/9 diagnostic profiles are supported.')
    info=story.require_leda(f)
    if bytes(f.payload[info.header+20:info.header+22]) not in (b'\x12\x05',b'\x10\x0b'):
        raise core.SaveError('Use a free-time or chapter-start source, not a battle/unknown resume state.')
    before=normalized_blocks(f)
    p=story.edited(f,chapter);p[info.header+20:info.header+22]=b'\x10\x0b'
    if profile=='C':
        schedule=one_block(f,'GameSchedule');calendar=one_block(f,'Calendar')
        if schedule.end-schedule.start!=24 or f.payload[schedule.start+4]!=1:
            raise core.SaveError('Unknown GameSchedule layout')
        if calendar.end-calendar.start!=16 or f.payload[calendar.start+4]!=6:
            raise core.SaveError('Unknown Calendar layout')
        old_clock=bytes(f.payload[schedule.start+5:schedule.start+12])
        if old_clock!=bytes(f.payload[info.header+22:info.header+29]):
            raise core.SaveError('Header and schedule clocks disagree')
        year=int.from_bytes(old_clock[:2],'little')
        if not 1<=year<=9999:raise core.SaveError('Invalid calendar year')
        month,day,hour=ENTRY_DATES[chapter]
        clock=struct.pack('<H5B',year,month,day,hour,0,0)
        p[info.header+22:info.header+29]=clock
        p[schedule.start+5:schedule.end]=clock+bytes(12)
        p[calendar.start+5:calendar.end]=bytes(11)
    if profile in ('B','C'):p=clear_restart(core.SaveFile(p))
    result=core.SaveFile(p);story.require_leda(result)
    after=normalized_blocks(result)
    allowed={'Header','GameUserData'}
    if profile in ('B','C'):allowed.add('GameRestartData')
    if profile=='C':allowed.update(('GameSchedule','Calendar'))
    if before.keys()!=after.keys() or any(before[n]!=after[n] for n in before.keys()-allowed):
        raise core.SaveError('An unrelated block changed')
    # GameUserData may change only the two fields from the original sequence edit.
    user=bytearray(before['GameUserData']);user[9]=chapter
    struct.pack_into('<Q',user,85,story.sequence(chapter))
    if bytes(user)!=after['GameUserData']:raise core.SaveError('Unexpected player/progression changes')
    return p


def build(source,output):
    source,output=Path(source),Path(output)
    if output.exists():raise ValueError('Use a fresh output directory')
    raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BASELINE_SHA256:
        raise ValueError('These probes require the unchanged accepted B0-01 baseline')
    original=container.SaveFile(str(source))
    if original.verify():raise ValueError('Invalid source checksums')
    f=core.SaveFile(original.payload);info=story.require_leda(f);story.check_outer(original.raw,info)
    if original.raw[48:57]!=bytes(f.payload[info.header+20:info.header+29]):
        raise ValueError('Source outer/live mode or clock disagree')
    ready=[]
    for name,chapter,profile in CASES:
        box=container.SaveFile(str(source));box.payload=edited_profile(f,chapter,profile)
        g=core.SaveFile(box.payload);i=story.read(g)
        summary=bytearray(box.raw);summary[48:57]=box.payload[i.header+20:i.header+29];box.raw=bytes(summary)
        data=box.to_bytes();ready.append((name,chapter,profile,data,bytes(box.payload)))
    output.mkdir(parents=True);(output/'00-Control').mkdir();(output/'00-Control/Auto').write_bytes(raw)
    records=[]
    for name,chapter,profile,data,payload in ready:
        folder=output/name;folder.mkdir();path=folder/'Auto';path.write_bytes(data)
        check=container.SaveFile(str(path));assert check.verify()==[] and bytes(check.payload)==payload
        g=core.SaveFile(check.payload);i=story.read(g);assert i.chapter==chapter
        assert check.raw[48:57]==bytes(g.payload[i.header+20:i.header+29])
        records.append({'case':name,'chapter':chapter,'profile':profile,'bytes':len(data),
                        'sha256':hashlib.sha256(data).hexdigest(),'game_test':'pending'})
    assert source.read_bytes()==raw
    report={'source_sha256':BASELINE_SHA256,'cases':records,'scope':'Diagnostic copies; no claim of working progression'}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.source,a.output),indent=2))
