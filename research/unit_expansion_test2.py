"""Build isolated experimental saves from a private Part 1 Leda baseline.

python research/unit_expansion_test2.py GAME_DATA LEDA_AUTO OUTPUT_DIRECTORY

Only derived metadata and this script belong in Git. Output contains private
saves. This does not unlock experimental characters in the editor catalogue.
"""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import argparse
import csv
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fefw_core as core
import fefw_save as container
import story_start
import unit_entries as entries
from research import unit_catalog_report as source

HERE = Path(__file__).resolve().parents[1]
PROFILES = {
    'PID_カストール': {},
    'PID_ロン': {},
    'PID_ヴァンダル': {'class_key': 'JID_セスタス'},
    'PID_マーズ': {'class_key': 'JID_ザ・ブレイド'},
    'PID_ソティス': {'class_key': 'JID_シャーマン', 'hp': 25,
                   'ranks': [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]},
}
# Exact IDs are recovered. Assignment of the extra items/spell is a test choice.
CASES = [
    ('X1-Cai', 'PID_カイ', None, 'Ordinary catalogue defaults; cross-route protagonist test.'),
    ('S1-Hong-Hua', 'PID_コウカ', None, 'Own recovered defaults; special-character source flags.'),
    ('S2-Troy', 'PID_トロイア', None, 'Own recovered defaults; special-character source flags.'),
    ('S3-Anna', 'PID_アンナ', 'IID_青銅の槍', 'Own class/HP/ranks; guessed Bronze Spear loadout. No explicit mount.'),
    ('S4-Centurio', 'PID_セントリオン', None, 'Own recovered defaults; different special-character source flags.'),
    ('N1-Castor', 'PID_カストール', None, 'Own Guardian/25 HP/ranks/items; serial zero, excluded by current filter.'),
    ('N2-Long', 'PID_ロン', None, 'Own Pugilist/24 HP/ranks/items; serial zero, excluded by current filter.'),
    ('N3-Vandahl', 'PID_ヴァンダル', 'IID_青銅の籠手', 'Pugilist selected from his class progression; own 26 HP/ranks, guessed Bronze Gauntlets loadout.'),
    ('S5-Mars', 'PID_マーズ', 'IID_青銅の剣', 'The Blade selected from his class progression; own 30 HP/ranks, guessed Bronze Sword loadout.'),
    ('N4-Sothis', 'PID_ソティス', None, 'Placeholder-like base row: guessed Shaman, 25 HP, first black-magic/infantry ranks and Fire.'),
]


def digest(b):
    return hashlib.sha256(b).hexdigest()


def read_json(name):
    return json.loads((HERE / name).read_text(encoding='utf8'))


def audit(directory):
    source.tables.BASE = Path(directory)
    person = source.tables.Data('Person.bin')
    rows = source.records(person)
    names = read_json('unit_ids.json')
    jobs = read_json('job_ids.json')
    catalogue = read_json('unit_catalog.json')['entries']
    ordinary, omitted = [], []
    all_rows = []
    for pid, at in rows.items():
        h = f'{core.id_hash(pid):08x}'
        label = names.get(h, {})
        serial, bits = person.b[at+48:at+50]
        short = person.string(person.q(at+40))
        job = person.string(person.q(at+56))
        hp = int.from_bytes(person.b[at+450:at+452], 'little', signed=True)
        reason = ('Enabled' if not catalogue[h]['restriction'] else 'Restricted') if h in catalogue else (
            'Serial zero / non-player or template candidate' if not serial else 'Serial outside 1–99')
        row = {'pid': pid, 'name': label.get('name', pid), 'name_evidence': label.get('src', 'unclassified'),
               'hash': h, 'serial': serial, 'source_flags': bits, 'short_id': short,
               'class_key': job, 'class': jobs.get(f'{core.id_hash(job):08x}', {}).get('en', job) if job else '',
               'hp': hp, 'catalogue_status': reason,
               'class_progression': source.array(person, at+72)}
        all_rows.append(row)
        if bits == 39:
            ordinary.append(row)
        # A browse list, not a claim of recruitability; includes named creatures.
        if h not in catalogue and pid.count('_') == 1 and (short or label.get('src') in ('exact', 'part')):
            omitted.append(row)
    missing = [r for r in ordinary if r['hash'] not in catalogue]
    if missing:
        raise ValueError('Ordinary-pattern candidates missing from catalogue: '+str(missing))
    return {'person_sha256': digest(person.b), 'person_rows': len(rows),
            'ordinary_pattern_count': len(ordinary), 'ordinary_pattern_missing': missing,
            'enabled': [r for r in all_rows if r['catalogue_status'] == 'Enabled'],
            'restricted': [r for r in all_rows if r['catalogue_status'] == 'Restricted'],
            'omitted_base_identities': omitted, 'all_rows': all_rows,
            'limits': 'Source flag 39 is a heuristic, not proven natural recruitability. Flag labels are generated from PIDs. Event availability and route/part eligibility remain unverified.'}


def build(directory, baseline, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    baseline = Path(baseline)
    original_bytes = baseline.read_bytes()
    box = container.SaveFile(str(baseline))
    if box.verify():
        raise ValueError('Baseline checksum failure')
    before = core.SaveFile(box.payload)
    info = entries.require_context(before)
    if info.route != 4:
        raise ValueError('Use the Leda baseline for this test set')
    original_catalogue = read_json('unit_catalog.json')
    if source.report(directory) != original_catalogue:
        raise ValueError('Source tables do not reproduce the current catalogue')
    # Preserve the historical Test 2 profiles, including mounted Anna.
    expanded = source.report(directory, extra_profiles=PROFILES, accepted_defaults=False)['entries']
    coverage = audit(directory)
    (output/'catalogue-audit.json').write_text(json.dumps(coverage, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    with (output/'all-person-records.csv').open('w', newline='', encoding='utf-8-sig') as fp:
        writer = csv.DictWriter(fp, fieldnames=list(coverage['all_rows'][0]))
        writer.writeheader(); writer.writerows(coverage['all_rows'])
    control = output/'test-saves'/'00-Control-Leda'/'Auto'
    control.parent.mkdir(parents=True); control.write_bytes(original_bytes)
    original_units = [before.tree().copy_object(before.tree().node_at(u.start), 0) for u in before.units()]
    original_blocks = story_start.normalized_blocks(before)
    original_flags = entries.flag_values(before)
    original_payload = bytes(before.payload)
    manifest = []
    items, jobs, skills = read_json('item_ids.json'), read_json('job_ids.json'), read_json('skill_ids.json')
    for case, pid, extra_item, evidence in CASES:
        h = core.id_hash(pid)
        row = deepcopy(expanded[f'{h:08x}'])
        if extra_item:
            item_hash = f'{core.id_hash(extra_item):08x}'
            if item_hash not in items:
                raise ValueError('Unknown item '+extra_item)
            row['items'].append(item_hash)
        if pid == 'PID_ソティス':
            magic = f'{core.id_hash("IID_ファイアー"):08x}'
            skill = f'{core.id_hash("SID_ファイアー"):08x}'
            if magic not in items or skill not in skills:
                raise ValueError('Fire identity missing')
            row['magic'] = [magic]
            row['skills'][5] = [skill]
        row['restriction'] = ''  # Only the single explicit research case, in memory.
        table = deepcopy(entries.catalog()); table[h] = row
        identities = {}
        for key, value in table.items():
            for alias in [key, *(int(x,16) for x in value['aliases'])]:
                if alias in identities and identities[alias] != key:
                    raise ValueError('Conflicting research identity')
                identities[alias] = key
        with patch.object(entries, 'catalog', return_value=table), patch.object(entries, 'identities', return_value=identities):
            result = core.SaveFile(entries.add(before, h))
            # All original units, unrelated blocks and flags must survive exactly.
            units = [result.tree().copy_object(result.tree().node_at(u.start), 0) for u in result.units()]
            if units[:-1] != original_units:
                raise ValueError('Original unit changed')
            blocks = story_start.normalized_blocks(result)
            for name in original_blocks.keys()-{'UnitPool', 'GameUserData'}:
                if blocks[name] != original_blocks[name]:
                    raise ValueError('Unrelated block changed: '+name)
            wanted = dict(original_flags)
            for key in (row['recruit_flag'], row['met_flag']):
                if key: wanted[core.id_hash(key)] = 1
            if entries.flag_values(result) != wanted:
                raise ValueError('Unexpected flag edit')
            try:
                entries.add(result, h)
            except core.SaveError:
                pass
            else:
                raise ValueError('Duplicate was allowed')
            rows = entries.roster(result)
            unit, gear = rows[-1]
            if (unit.person != h or unit.klass != int(row['class'], 16)
                    or result.payload[unit.level_off] != 1
                    or result.u16(unit.hp_off) != row['hp']
                    or unit.stats != [0]*9 or unit.counters
                    or unit.masteries != [tuple(x) for x in row['masteries']]
                    or unit.skill_lists != [[int(x,16) for x in group] for group in row['skills']]):
                raise ValueError('Experimental defaults did not read back')
            if len({g.unit_number for _,g in rows}) != len(rows):
                raise ValueError('Duplicate unit number')
            case_path = output/'test-saves'/case/'Auto'
            case_path.parent.mkdir(parents=True)
            box.payload = result.payload
            case_path.write_bytes(box.to_bytes())
            reread = container.SaveFile(str(case_path))
            if reread.verify() or reread.payload != result.payload:
                raise ValueError('Container round-trip failure')
            if bytes(before.payload) != original_payload or baseline.read_bytes() != original_bytes:
                raise ValueError('Baseline was changed')
            manifest.append({'case': case, 'name': row['name'], 'pid': pid, 'unit_number': gear.unit_number,
                'level': 1, 'class': jobs[row['class']]['en'], 'hp': row['hp'],
                'inventory': [items[x].get('en') or items[x].get('jp') for x in row['items']+row['magic']],
                'recruit_flag': row['recruit_flag'], 'met_flag': row['met_flag'],
                'defaults_note': evidence, 'profile': row,
                'sha256': digest(case_path.read_bytes()), 'checksum_errors': [],
                'validation': 'Original units/other blocks/other flags unchanged; duplicate refused; unique number; container round-trip passed.'})
    # The patched catalogue must never escape the case context.
    if {f'{k:08x}':v for k,v in entries.catalog().items()} != original_catalogue['entries']:
        raise ValueError('Runtime catalogue changed')
    if (output/'test-saves'/'00-Control-Leda'/'Auto').read_bytes() != original_bytes:
        raise ValueError('Control changed')
    (output/'test-saves'/'manifest.json').write_text(json.dumps({
        'baseline_sha256': digest(original_bytes), 'route': info.route, 'chapter': info.chapter,
        'checks': 'All ten cases passed structural checks; no game acceptance yet.',
        'cases': manifest}, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    write_guide(output, coverage, manifest)
    return {'cases': len(manifest), 'route': info.route, 'chapter': info.chapter,
            'baseline_sha256': digest(original_bytes), 'ordinary_pattern': coverage['ordinary_pattern_count'],
            'person_rows': coverage['person_rows'], 'omitted_base_identities': len(coverage['omitted_base_identities'])}


def write_guide(output, coverage, cases):
    text = '''# New units — expanded tests 2

These are ten independent pre-edited saves, each adding ONE unit to the same
old Leda Chapter 9 baseline. Use the existing restoration-fix editor if needed;
there is no new editor build to install and no need to enable restricted rows.
Only the experimental save has the added character. Main has not been merged.

## Install and return

Close the game, keep your original save folder, and install one case's Auto
at a time into a disposable copy. Keep its companion files/other slots. The
00-Control-Leda Auto is byte-for-byte unchanged. Every case deliberately uses
the same free unit number because the cases are separate; do not combine them.
Load the named case before each test, rather than continuing the previous case.

For each case:

1. Check load, roster, portrait/model, class, HP, inventory and skills.
2. Save and reload. If saving is unavailable at arrival, continue to the next
   opportunity; do not count that alone as a failure.
3. Deploy the added character with Leda and an original party member. Select,
   move/cancel, then act/attack. Check ownership and animations. Gain EXP/a
   level if practical. For Cai, also verify Leda remains the route protagonist
   and the next story objective progresses normally.
4. Save/reload after combat and repeat selection. Return Auto-after-progress
   under the case folder, or describe precisely where it failed. A load crash,
   missing model, undeployable unit or broken action is useful evidence; skip
   that case and restore the control. Do not spend time repairing it manually.

Suggested order: X1, S1–S4, N1–N3, S5, then N4. Sothis is the least supported
profile and may fail even to load. Deployment, progression and save/reload
should be reported separately; a roster appearance alone is not a full pass.

## Cases and default choices

All units start at level 1 with zero earned stat gains and a fresh unit number.
High ranks on special characters come from their own tables; they are not a
claim about their natural recruitment level. No mounts/battalions are explicitly
created, and no story, support, facility or class-unlock flags are granted.
The normal generator's conditional and forced/scripted skill grants remain
excluded; the game may derive additional character/class effects itself.
For NPCs, recruitment/met flag names are inferred from their exact PID, not
proof of real recruitment events. No flag is added merely to advance a quest.

| Case | Character | Class / HP | Default evidence and guesses |
|---|---|---|---|
'''
    for row in cases:
        text += f"| {row['case']} | {row['name']} | {row['class']} / {row['hp']} | {row['defaults_note']} |\n"
    text += '''
## What this establishes

A pass establishes this profile on this baseline, not all routes or later
natural recruitment. In particular, Cai's story identity may still affect a
later scripted event. Sothis's guessed class/stats are a playability experiment,
not recovered canonical defaults. The production Add unit list stays unchanged
until results establish which entries should be exposed and how to label them.

See CATALOGUE-COVERAGE.md for the full enabled/restricted list and omitted base
identities. catalogue-audit.json and all-person-records.csv preserve the audit;
test-saves/manifest.json records exact profiles, hashes and validation evidence.
'''
    (output/'START-HERE.md').write_text(text, encoding='utf8')
    doc = f'''# Catalogue coverage audit

Audited {coverage['person_rows']} Person rows from the supplied game tables.
The current catalogue has {len(coverage['enabled'])} enabled and {len(coverage['restricted'])} restricted identities.
All {coverage['ordinary_pattern_count']} rows with source flag byte 39 are accounted for:
54 enabled plus Eshmel, the restricted custom protagonist. This is exhaustive
for that data pattern, NOT a verified list of everyone naturally recruitable.

The earlier generator checks serials 1–99 and the presence of a generated
Recruited label. build_flag_names.py synthesizes recruitment/met keys from
unit_ids.json, so such a label is not independent recruitment evidence.
Six positive serials 100–105 are omitted: Jurah, Mars, Smyrnos, Credna, Kalla,
Aurora. They have different flags and missing single starting classes; this
does not establish that they are missing normal recruits. Castor and Long
have usable class/HP data but serial zero. Many other named rows have no
combat defaults at all. No NPC was deleted from the game or broad identity
dictionary: these rows were excluded from the Add unit picker.

To establish complete normal-recruit coverage, trace actual recruitment
events/conditions across routes and parts, canonicalize scenario variants,
compare naturally recruited saves, and validate each missing identity's
creation/deployment/persistence and later recruitment behavior. Do not expand
the normal list simply because a character has a name or recruitment label.
Custom Eshmel also needs appearance/avatar initialization research.

## Enabled ordinary-pattern candidates

'''+', '.join(r['name'] for r in coverage['enabled'])+'.\n\n## Restricted identities already in the picker\n\n'+', '.join(r['name'] for r in coverage['restricted'])+'''.

## Other base identities to browse

This list includes named NPCs, placeholders and creatures; names from partial
matches retain that evidence label. It is not a recruit list. Every one of the
2,923 source rows, including generic/scenario variants, is in the CSV/JSON.
Blank class or zero HP means further defaults are needed, not proof the actor
can never be playable. Names with a source flag other than 39 are unclassified
for natural recruitment until stronger evidence is available.

| Name | Name evidence | Serial | Source flags | Starting class | HP |
|---|---|---:|---:|---|---:|
'''
    for row in coverage['omitted_base_identities']:
        doc += f"| {row['name']} | {row['name_evidence']} | {row['serial']} | {row['source_flags']} | {row['class'] or 'Not set'} | {row['hp']} |\n"
    (output/'CATALOGUE-COVERAGE.md').write_text(doc, encoding='utf8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('gamedata', type=Path)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.gamedata, args.baseline, args.output), indent=2))
