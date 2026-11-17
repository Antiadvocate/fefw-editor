"""Inspect the shared private Part 2 timeline; never distribute game bytes.

One common timeline supports testing the same sequence targets across routes.
It does not prove each route's entry or objectives work with a Part 1 baseline.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research import facility_access_report as data


def report(gamedata):
    data.BASE = Path(gamedata)
    d = data.Data('Timeline_Part2.bin')
    schemas = [s for s in d.schemas if any(n == 'ハッシュキー' for n, t, z, o in s['fields'])]
    if len(schemas) != 1:
        raise ValueError('Expected one timeline schema')
    schema = schemas[0]; rows = []
    for ref in d.refs_to_string('戦争篇'):
        at = ref-8
        if at < schema['end'] or at+schema['stride'] > len(d.b):
            continue
        row = {n: v for n, t, o, v in d.values(at, schema)}
        if isinstance(row['引数'], list):
            rows.append((at, row))
    starts = [r for _, r in rows if r['引数'] == ['2部開始']]
    if len(starts) != 1 or starts[0]['部'] != 2 or starts[0]['年'] != 1450:
        raise ValueError('Unexpected shared Part 2 start')
    chapters = []
    for at, row in rows:
        args = row['引数']
        match = re.fullmatch(r'MCID_2_title(\d\d)', args[0]) if len(args) == 1 else None
        if row['種類'] != 10 or not match:
            continue
        chapter = int(match[1]); clock = starts[0] if chapter == 1 else row
        chapters.append({'chapter': chapter, 'offset': hex(at), 'title': args[0],
                         'month': clock['月'], 'day': clock['日'], 'time': clock['時刻']})
    if [r['chapter'] for r in chapters] != list(range(1, 7)):
        raise ValueError('Expected six shared title rows')
    return {'source': 'Timeline_Part2.bin', 'sha256': hashlib.sha256(d.b).hexdigest(),
            'group': '戦争篇', 'year': 1450, 'chapters': chapters,
            'route_specific_start': any('2部セオドラ用初期位置' in r['引数'] for _, r in rows),
            'scope': 'Shared chapter structure and dates only; non-Cai sequence reuse and progression remain inferred.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('gamedata', type=Path)
    print(json.dumps(report(p.parse_args().gamedata), ensure_ascii=False, indent=2))
