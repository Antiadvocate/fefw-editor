"""Build two class-only Anna retests from the original private S3 Auto.

python research/anna_deployment_test3.py GAME_DATA S3_AUTO OUTPUT
Never publish the generated saves. No production catalogue changes are made.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import story_start
import unit_entries as entries
from research import unit_catalog_report as tables

ANNA = core.id_hash('PID_アンナ')
CASES = [('A0-Original-Elephant', 'JID_戦象兵'),
         ('A1-Dismounted-Anna', 'JID_戦象兵下馬'),
         ('A2-Soldier-Anna', 'JID_兵士')]


def build(gamedata, baseline, output):
    source = Path(baseline).read_bytes()
    box = container.SaveFile(str(baseline))
    if box.verify(): raise ValueError('Baseline checksum failure')
    f = core.SaveFile(box.payload)
    info = entries.require_context(f)
    if info.route != 4 or info.chapter != 9: raise ValueError('Use the Leda Chapter 9 S3 input')
    rows = entries.roster(f); hits = [(u,g) for u,g in rows if u.person == ANNA]
    if len(hits) != 1: raise ValueError('Expected exactly one Anna')
    anna, gear = hits[0]
    if anna.klass != core.id_hash('JID_戦象兵') or gear.ride or gear.legion:
        raise ValueError('Expected original unmounted-equipment S3 profile')
    original_blocks = story_start.normalized_blocks(f)
    original_items = core.unit_items(f, anna)
    tables.tables.BASE = Path(gamedata)
    jobs = tables.tables.Data('Job.bin'); jrows = tables.records(jobs)
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    results = []
    for case, key in CASES:
        if key not in jrows: raise ValueError('Missing class')
        cid = core.id_hash(key)
        work = f.copy()
        if cid != anna.klass:
            classes = list(anna.classes)
            if not any(c == cid for c,_,_ in classes): classes.append((cid,0,4))
            work = core.SaveFile(core.with_lists(work, anna, anna.masteries, classes))
            current = next(u for u in work.units() if u.person == ANNA)
            core.set_class(work, current, cid)
        got = entries.roster(work)
        if [(u.person,g.unit_number) for u,g in got] != [(u.person,g.unit_number) for u,g in rows]:
            raise ValueError('Identity changed')
        for (old,_),(new,_) in zip(rows,got):
            if old.person != ANNA:
                if f.tree().copy_object(f.tree().node_at(old.start),0) != work.tree().copy_object(work.tree().node_at(new.start),0):
                    raise ValueError('Other unit changed')
        current = next(u for u,g in got if u.person == ANNA)
        if current.klass != cid or current.masteries != anna.masteries or current.skill_lists != anna.skill_lists:
            raise ValueError('Unexpected Anna defaults')
        if core.unit_items(work,current) != original_items: raise ValueError('Inventory changed')
        # Reverse only the intended class and registered-class edits. Complete
        # payload equality proves all other Anna fields and save data survived.
        reverse = work.copy()
        core.set_class(reverse,current,anna.klass)
        reverse = core.SaveFile(core.with_lists(reverse,current,anna.masteries,anna.classes))
        if reverse.payload != f.payload: raise ValueError('Non-class data changed')
        blocks = story_start.normalized_blocks(work)
        if any(blocks[k] != v for k,v in original_blocks.items() if k != 'UnitPool'):
            raise ValueError('Unrelated block changed')
        folder=output/'test-saves'/case;folder.mkdir(parents=True)
        box.payload=work.payload
        encoded=source if cid==anna.klass else box.to_bytes()
        (folder/'Auto').write_bytes(encoded)
        checked=container.SaveFile(str(folder/'Auto'))
        if checked.verify() or checked.payload != work.payload: raise ValueError('Round-trip failure')
        at=jrows[key]
        results.append({'case':case,'class_key':key,'class_hash':f'{cid:08x}',
                        'unit_number':gear.unit_number,'deployment_field':jobs.b[at+96],
                        'footprint_field':jobs.b[at+417],
                        'sha256':hashlib.sha256(encoded).hexdigest(),
                        'changes':[] if cid==anna.klass else ['Anna current class','Anna registered classes'],
                        'checksums':checked.verify()})
    if Path(baseline).read_bytes() != source: raise ValueError('Input changed')
    report={'source_sha256':hashlib.sha256(source).hexdigest(),'cases':results,
            'validation':'All checks pass; exact source recovered by reversing class edits. No game pass claimed.'}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('gamedata',type=Path);p.add_argument('baseline',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(build(a.gamedata,a.baseline,a.output),indent=2))
