"""Diagnose known chapter prerequisites without replaying a chapter.

Rules are limited to the access/teaching/map repairs established in game tests.
Detection is read-only; applying a suggestion preserves the current story beat,
clock, restart snapshots and party. Unknown parts never inherit Part 1 rules.
"""
from dataclasses import dataclass

import facilities
import fefw_core as core
import story
import story_start
import story_prerequisites as dietrich
import story_theodora_prerequisites as theodora
import worldmap

ISSUES_URL = 'https://github.com/Antiadvocate/fefw-editor/issues'


@dataclass(frozen=True)
class Rule:
    note: str
    switches: tuple = ()
    secret: bool = False
    map_exit: bool = False


@dataclass(frozen=True)
class Check:
    label: str
    state: str
    needed: bool


@dataclass(frozen=True)
class Diagnosis:
    progress: story.Progress
    note: str
    checks: tuple = ()
    blocked: str = ''

    @property
    def actionable(self):
        return not self.blocked and any(row.needed for row in self.checks)


def rule_for(info):
    if info.route not in story.PREFIXES:
        return None
    if info.part == 2:
        if info.chapter == 5:
            return Rule('Upper-city movement opens the route to Dagda’s temple. '
                        'Chapter 5 progression passed on all four routes.',
                        (story_start.PART2_UPPER_MOVEMENT,))
        if info.chapter == 6:
            return Rule('Middle-city movement opens the midtown gate toward Dagda’s cauldron. '
                        'Theodora’s repaired save and fresh chapter entry both passed; '
                        'the other routes already had this access in their successful tests.',
                        (story_start.PART2_MIDDLE_MOVEMENT,))
        return None
    if info.part != 1:
        return None
    if info.route == 1 and 3 <= info.chapter <= 12:
        return Rule('Enables the Sewers entrance dialogue prerequisite. Cai Chapter 4 '
                    'entry and progression passed; the entrance still depends on the story phase.',
                    (facilities.SEWERS,))
    if info.route == 2 and info.chapter in (5, 6):
        switches = tuple(h for changes in dietrich.CHAPTER_EDITS[info.chapter].values()
                         for h in changes)
        note = ('Upper-city movement allows the certification objective to progress.'
                if info.chapter == 5 else
                'Lower-city movement, upper/lower area access and Vandahl Trading Company '
                'access let the trading-company objective progress. The upper movement '
                'restriction is intentionally retained.')
        return Rule(note + ' Direct entry and progression passed.', switches)
    if info.route == 2 and info.chapter == 7:
        return Rule('Allows Hidden Windpierce teaching. Teaching Esmerelda and reaching '
                    'the next checkpoint passed. This does not add a recipient or teach the skill.',
                    secret=True)
    if info.route == 3 and info.chapter in theodora.CITY:
        note = {4: 'Middle-city movement allows access to the arena gate.',
                6: 'City movement enables an alternate route to the objective. '
                   'The NPC barrier may remain; use the accessible route around it.',
                8: 'City movement cleared the NPC barrier and allowed progression in the tested save. '
                   'Other story phases or times may behave differently.'}[info.chapter]
        return Rule(note + ' Chapter progression passed.', theodora.CITY[info.chapter])
    if info.route == 3 and info.chapter == 9:
        return Rule('Shows the three-point connection out of Troy’s Shrine toward Wandering Wood. '
                    'Map movement and progression passed. Visited state is preserved.', map_exit=True)
    return None


def diagnose(f):
    info = story.read(f)
    rule = rule_for(info)
    if rule is None:
        note = 'No established progress repair for this character, part and chapter.'
        if info.part == 3:
            note += ' No established Part 3 progress repair is available yet.'
        elif info.route == 2 and info.part == 1 and info.chapter in (1, 2):
            note += ' Dietrich Chapter 2 replay can block at Esmerelda’s rescue; '
            note += 'the attempted flag repairs failed. Chapter 1 leads into that block.'
        elif (info.route, info.part, info.chapter) == (4, 1, 1):
            note += ' Leda Chapter 1 replay can block at its first objective; no reliable repair is known.'
        return Diagnosis(info, note)
    checks = []
    try:
        if rule.switches:
            values = facilities.read(f)
            maps = {m: facilities.locate_member(f, m)
                    for m in {facilities.member_for(h) for h in rule.switches}}
            for h in rule.switches:
                if any(v.hash == h and v.wide for v in maps[facilities.member_for(h)].flags):
                    raise core.SaveError('Unknown wide value for ' + facilities.catalog()[h]['label'])
                state = facilities.enabled(h, values.get(h))
                if state is None:
                    raise core.SaveError('Unknown value for ' + facilities.catalog()[h]['label'])
                checks.append(Check(facilities.catalog()[h]['label'],
                                    'Already enabled' if state else 'Disabled → enable', not state))
        if rule.secret:
            rows = {v.hash: v for v in facilities.locate_member(f, dietrich.PROGRESSION).flags}
            row = rows.get(dietrich.SECRET)
            if row and (row.wide or row.value not in (0, 1)):
                raise core.SaveError('Unknown Hidden Windpierce permission value.')
            active = row is not None and row.value == 1
            checks.append(Check('Hidden Windpierce teaching permission',
                                'Already enabled' if active else 'Disabled → enable', not active))
        if rule.map_exit:
            recs = worldmap.read(f)
            for key, label in zip(theodora.TROY_EXIT, ('Troy’s Shrine', 'Junction 374', 'Wandering Wood')):
                row = recs.get(key)
                if not row or not row.editable or row.state not in (1, 2, 3):
                    raise core.SaveError('Unknown Troy exit map record: ' + label)
                active = row.state == worldmap.SHOWN
                checks.append(Check(label, 'Already shown' if active else 'Not shown → show', not active))
    except (core.SaveError, worldmap.MapError) as exc:
        return Diagnosis(info, rule.note, tuple(checks), 'Cannot safely inspect this repair: ' + str(exc))
    try:
        story_start.validate(f)
    except core.SaveError:
        return Diagnosis(info, rule.note, tuple(checks),
                         'Suggestions are read-only in this save state. Use a supported free-time '
                         'or chapter-start save to apply them.')
    return Diagnosis(info, rule.note, tuple(checks))


def edited(f):
    report = diagnose(f)
    if report.blocked:
        raise core.SaveError(report.blocked)
    if not report.actionable:
        return bytearray(f.payload)
    rule = rule_for(report.progress)
    if rule.switches:
        result = facilities.edited(f, {h: True for h in rule.switches})
    elif rule.secret:
        result = dietrich.edited(f, report.progress.chapter)
    else:
        result = theodora.edited(f, report.progress.chapter)
    # Repair writers are scoped; independently guard story identity and all
    # unrelated roots, including live clocks and embedded restart snapshots.
    after = core.SaveFile(result)
    current = story.read(after)
    if (current.route, current.part, current.chapter, current.sequence) != (
            report.progress.route, report.progress.part, report.progress.chapter, report.progress.sequence):
        raise core.SaveError('Repair changed story progress; no changes applied.')
    before_roots, after_roots = story_start.normalized_blocks(f), story_start.normalized_blocks(after)
    allowed = {'GmapSpotMgr'} if rule.map_exit else {'GameUserData'}
    if before_roots.keys() != after_roots.keys() or any(
            before_roots[k] != after_roots[k] for k in before_roots.keys()-allowed):
        raise core.SaveError('Repair changed unrelated data; no changes applied.')
    return bytearray(result)
