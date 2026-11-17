"""Read-only Dagsion access evidence from Hub/HubDispos, separate from flags.

The four locators' protagonist filters explain the previous Leda travel test.
A matching route is necessary for a filtered locator, not a full access check.
"""
import fefw_core as core
import fefw_layer as layer
import fast_travel
import facilities

ROOM = 0x38574e83
GARDEN = 0x1e4d4a23
SALAMIS = 0xefb57d93
YU_PHAS = 0x65411bed
YU_PHAS_GATE = 0x7d2c41eb

CONDITIONS = {
    '行動範囲制限_上層': 'Movement restricted: Dagsion upper area (separate from function unlock)',
    '行動範囲制限_中層': 'Movement restricted: Dagsion middle area (separate from function unlock)',
    '行動範囲制限_下層': 'Movement restricted: Dagsion lower area / port (separate from function unlock)',
    '行動範囲制限_富裕区-商業区': 'Movement restricted: wealthy–commercial district passage',
    '拠点_カイ篇1部2章_行動制限3': 'Story restriction: Cai P1 Ch2, group 3',
    '拠点_カイ篇1部11章_行動制限2': 'Story restriction: Cai P1 Ch11, group 2',
    '拠点_カイ篇1部11章_行動制限3': 'Story restriction: Cai P1 Ch11, group 3',
    '拠点_カイ篇1部11章_行動制限4': 'Story restriction: Cai P1 Ch11, group 4',
    '拠点_セオドラ篇1部6章_行動制限1': 'Story restriction: Theodora P1 Ch6, group 1',
    '拠点_セオドラ篇1部11章_行動制限1': 'Story restriction: Theodora P1 Ch11, group 1',
    '拠点_セオドラ篇1部11章_行動制限3': 'Story restriction: Theodora P1 Ch11, group 3',
    '2部5章_行動制限1': 'Story restriction: P2 Ch5, group 1',
    '2部6章_行動制限1': 'Story restriction: P2 Ch6, group 1',
    '大釜部屋解放': 'Cauldron room unlocked (access-condition flag)',
    '拠点_Hub_000_A60_アウロラ神殿側ドア開放': 'Door opened: A60, Aurora temple side',
    '拠点_Hub_000_A60_地下牢側ドア開放': 'Door opened: A60, dungeon side',
}

DETAILS = {
    ROOM: ('Cai', 'Walking entry has story conditions',
           'The fast-travel locator requires Cai (KAI). The A60 walking entrance uses story restrictions separately. The two A60 door-open flags are referenced by Cai-only door events; they are not a general room-unlock switch.'),
    GARDEN: ('Cai', 'Walking entry has story conditions',
             'The fast-travel locator requires Cai (KAI). A60 has normal, red-line and hidden-name variants selected by story restrictions. A stored travel flag alone cannot remove this route filter.'),
    SALAMIS: ('Theodora', 'Entrance also requires Theodora',
              'Both the fast-travel locator and A1-to-A9 entrance require Theodora (SEO). The entrance also checks P1 Ch6/Ch11 action restrictions. Registering the travel flag does not change these conditions.'),
    YU_PHAS: (None, 'Main entrance has route/chapter checks',
              'The travel locator has no protagonist filter. Main-entrance rows include Theodora P1 Ch12 during free time and Eshmel (ISM). Separate block rows apply to Cai, Dietrich and Leda. An A140 inner entrance has a free-time condition. Travel/exit passed on Leda P1 Ch9; walking back in was blocked. No route, chapter or action-restriction flags are changed here.'),
}


def apply_labels(names):
    updates = {}
    for key, label in CONDITIONS.items():
        h = core.id_hash(key)
        if names.get(h, {}).get('name', key) != key:
            raise core.SaveError(f'Conflicting access-condition identity for {h:08x}')
        updates[h] = {**names.get(h, {}), 'name': key, 'label': label}
    names.update(updates)


def route_info(f):
    try:
        return layer.route_info(f.payload)
    except (IndexError, core.SaveError):
        return None


def yu_phas_gate_status(f):
    """Report the separately saved switches, without granting either one."""
    try:
        gate = facilities.read(f).get(YU_PHAS_GATE)
    except core.SaveError:
        return 'Yu Phas gate: cannot identify the facility map.'
    if gate not in (None, 0, 1):
        return f'Yu Phas gate: unknown registration value ({gate}); preserved.'
    if gate != 1:
        return 'Yu Phas gate: registration is not enabled.'
    try:
        travel = fast_travel.read(f).get(YU_PHAS)
    except core.SaveError:
        return 'Yu Phas gate: registered; cannot check its ordinary travel flag.'
    if travel is None:
        return 'Yu Phas gate: registered; also enable Yu Phas Temple in Fast travel.'
    if travel != 1:
        return f'Yu Phas gate: registered; unknown ordinary travel value ({travel}); preserved.'
    return 'Yu Phas gate: both flags recorded. Listing and portal use passed on Leda P1 Ch9.'


def report(f):
    route = route_info(f)
    try:
        values, error = fast_travel.read(f), ''
    except core.SaveError as exc:
        values, error = {}, str(exc)
    rows = []
    for h, (required, entry, detail) in DETAILS.items():
        gate = ('Unknown route' if route is None else
                'No locator route filter' if required is None else
                'Route matches; other conditions may apply' if route[0] == required else
                f'Route mismatch: requires {required}')
        value = values.get(h)
        stored = ('Unavailable' if error else 'Absent' if value is None else
                  'Recorded (1)' if value == 1 else f'Unknown ({value})')
        gate_status = yu_phas_gate_status(f) if h == YU_PHAS else ''
        if gate_status:
            detail += '\n' + gate_status
        rows.append({'hash': h, 'label': fast_travel.catalog()[h]['label'],
                     'stored': stored, 'route_check': gate, 'entry': entry,
                     'detail': detail, 'error': error, 'gate_status': gate_status})
    try:
        values = facilities.read(f)
        training = facilities.state_label(0xd70afcb2, values.get(0xd70afcb2))
        practice = facilities.state_label(0x728ccd68, values.get(0x728ccd68))
        detail = f'Training switch: {training}. Mentoring switch: {practice}. '
    except core.SaveError:
        detail = 'Related saved switches could not be read. '
    rows.append({'id': 'arena', 'hash': None, 'label': 'Arena',
                 'stored': 'Switch not mapped', 'route_check': 'Distinct from Training',
                 'entry': 'Story and opening hours apply', 'error': '', 'gate_status': '',
                 'detail': detail + 'Game data defines Arena and Training separately. The ordinary arena receptionist checks Arena access; both facility schedules close from 00:00 to 06:00. No independent Arena save flag has been established, and Training is not a proven substitute. Chapter 9 enabled multiple functions together, so that observation does not isolate the cause. The Chapter 4 objective is in the underground area, not proof that the spectating service is required.'})
    return rows


def diagnostics(f):
    route = route_info(f)
    lines = ['Function access diagnostics', 'Route: ' + (
        f'{route[0]} P{route[1]} Ch{route[2]}' if route else 'unknown'),
        'Stored switches and data conditions are not a guarantee of game access.', '']
    for row in report(f):
        lines.append(f"{row['label']}: {row['stored']}; {row['route_check']}; {row['entry']}")
        if row['gate_status']:
            lines.append(row['gate_status'])
        if row['error']:
            lines.append(row['error'])
    lines += ['', 'Related saved flags (read-only; missing means no stored record):']
    maps = core.flag_maps(f)
    for key, label in CONDITIONS.items():
        h = core.id_hash(key)
        hits = [(m.index, v.value) for m in maps for v in m.flags if v.hash == h]
        state = ', '.join(f'list {i}: {v}' for i, v in hits) or 'absent'
        lines.append(f'{label}: {state} [{h:08x}]')
    return '\n'.join(lines)
