"""Chapter entry for tested Part 1 routes and provisional Part 2.

Leda Chapters 2–12 have short-session game evidence. Chapter 1 is unavailable:
its opening plays but its first objective cannot be progressed.
No private captures or GameData are required at runtime.
Cai Part 2 Chapters 1–6 passed opening and next-battle checks.
Chapter 5 upper-city movement repair passed both resumed and fresh entry.
Part 1 Chapter 4-to-Part 2 Chapter 1 entry passed short-session checks;
other conversion starting states and long-term progression remain untested.
Leda, Dietrich and Theodora Part 2 Chapters 1–6 reached the next battle from
their tested Part 1 baselines. Theodora Chapter 6 needed a manual middle-city
movement repair; the automatic chapter-entry repair subsequently passed its retest.
Cai Part 1 Chapters 1–12 passed short-session game tests.
Dietrich Chapters 3–12 passed short-session checks, including integrated
prerequisites for 5–7. Chapters 1/2 are unavailable: Chapter 2 replay remains
blocked, and Chapter 1 leads into that block. Native saves still load normally.
Theodora Chapters 1–12 passed short-session checks, with Test 2 repairs for
4/6/8/9. Chapter 6 passes via alternate traversal; its NPC barrier can remain.
Chapters 1–2 use 1446; Chapter 3+ uses 1449 regardless of the source year.
"""
from datetime import datetime
import struct

import fefw_core as core
import story
import facilities
import story_prerequisites
import story_theodora_prerequisites

CHAPTERS = tuple(range(2, 13))
TESTED = frozenset(CHAPTERS)
# Chapter 1's title inherits its date; use the captured natural checkpoint.
# Later chapters return to 1449, including when the source is Chapter 1.
ENTRY_YEARS = {chapter: 1444 if chapter == 1 else 1449 for chapter in range(1, 13)}
ENTRY_DATES = {1: (12, 1, 12, 0), 2: (1, 2, 12, 0), 3: (1, 20, 20, 0),
               4: (3, 1, 8, 0), 5: (4, 6, 12, 0), 6: (5, 8, 12, 0),
               7: (5, 28, 20, 0), 8: (6, 29, 11, 0), 9: (7, 10, 18, 0),
               10: (9, 28, 2, 0), 11: (10, 16, 12, 0), 12: (11, 7, 12, 0)}
CAI_DATES = {1: (1, 24, 2, 0), 2: (1, 25, 11, 0), 3: (2, 4, 8, 0),
             4: (3, 1, 12, 0), 5: (3, 14, 12, 0), 6: (4, 19, 10, 0),
             7: (6, 9, 12, 0), 8: (7, 10, 12, 0), 9: (9, 3, 12, 0),
             10: (9, 15, 12, 0), 11: (10, 16, 8, 0), 12: (11, 3, 12, 0)}
DIETRICH_DATES = {1: (2, 10, 9, 0), 2: (2, 10, 14, 0), 3: (2, 11, 12, 0),
                  4: (3, 8, 12, 0), 5: (4, 11, 6, 0), 6: (5, 4, 12, 0),
                  7: (5, 29, 20, 0), 8: (6, 21, 12, 0), 9: (8, 10, 12, 0),
                  10: (9, 29, 12, 0), 11: (10, 5, 12, 0), 12: (11, 4, 12, 0)}
DIETRICH_CHAPTERS = tuple(range(3, 13))
THEODORA_DATES = {1: (2, 1, 12, 0), 2: (2, 13, 12, 0), 3: (2, 4, 7, 0),
                  4: (3, 1, 12, 0), 5: (3, 7, 20, 0), 6: (3, 21, 23, 0),
                  7: (4, 21, 5, 0), 8: (6, 1, 12, 0), 9: (7, 1, 12, 0),
                  10: (8, 25, 12, 0), 11: (9, 17, 12, 0), 12: (10, 16, 10, 0)}
THEODORA_YEARS = {chapter: 1446 if chapter <= 2 else 1449 for chapter in range(1, 13)}
TARGETS = {4: CHAPTERS, 1: tuple(CAI_DATES), 2: DIETRICH_CHAPTERS, 3: tuple(THEODORA_DATES)}
TESTED_BY_ROUTE = {4: TESTED, 1: frozenset(CAI_DATES),
                   2: frozenset(DIETRICH_CHAPTERS), 3: frozenset(THEODORA_DATES)}
THEODORA_REPAIRS = {
    4: 'Arena gate and progression passed with middle movement enabled',
    6: 'Progression passed via alternate city route; NPC barrier may remain',
    8: 'NPC barrier cleared and progression passed with city movement enabled',
    9: 'Troy exit and progression passed with three map points shown',
}
DIETRICH_BLOCKERS = {
    1: 'Battle works, but leads into the Chapter 2 rescue block',
    2: 'Replay cannot progress the rescue proximity event',
}
RESUME_OFFSET = 58
FREE_TIME_ID = 0xd8588d186b3f9502
CHECKPOINT_ID = 0xa2f3e9a7ff461708

RESTART_KEYS=frozenset((0x0db29669,0x1e2fc0a5,0xa23565e2,0x9fd3e608,0xa23565e3,0x1475b227,0xa23565e0,0x8c8807e8))
HEADER_KEY=core.fnv1_32(b'Header')
DATA_KEY=core.fnv1_32(b'Data')


def one_block(f,name):
    hits=[b for b in f.blocks if b.name==name]
    if len(hits)!=1:raise core.SaveError('Expected one '+name)
    return hits[0]


def members(f,tree,at,keys):
    index=tree.node_at(at)
    if index<0 or not tree.nodes[index].struct:raise core.SaveError('Expected a restart struct')
    node=tree.nodes[index];table=f.ptr(at);count=f.u32(at)>>24
    if count!=len(keys) or table+8*count!=node.end:raise core.SaveError('Unknown restart member layout')
    rows=[(f.u32(table+8*i),f.ptr(table+8*i+4)) for i in range(count)]
    if set(k for k,v in rows)!=keys or len({v for k,v in rows})!=count:
        raise core.SaveError('Missing or duplicate restart members')
    if set(v for k,v in rows)!={n.start for n in tree.nodes if n.parent==index}:
        raise core.SaveError('Unexpected restart children')
    return dict(rows)


def restart_leaves(f):
    tree=f.tree();block=one_block(f,'GameRestartData')
    slots=members(f,tree,block.start,RESTART_KEYS)
    if f.payload[block.start+4:block.start+8]!=b'\x03\0\0\0':
        raise core.SaveError('Unknown restart version/prefix')
    leaves=[]
    for at in slots.values():
        fields=members(f,tree,at,{HEADER_KEY,DATA_KEY})
        for key,start in fields.items():
            index=tree.node_at(start)
            node=tree.nodes[index]
            if node.struct or any(n.parent==index for n in tree.nodes):
                raise core.SaveError('Unexpected restart blob structure')
            body=bytes(f.payload[start+4:node.end])
            if len(body)<4 or int.from_bytes(body[:4],'little')!=len(body)-4:
                raise core.SaveError('Invalid restart blob length')
            data=body[4:]
            if key==HEADER_KEY and len(data) not in (0,256):
                raise core.SaveError('Unknown restart Header size')
            if data and any(data):
                if len(data)<32 or int.from_bytes(data[:4],'little')!=core.MAGIC:
                    raise core.SaveError('Unknown restart blob encoding')
                size,checksum,kind=struct.unpack_from('<III',data,4)
                if kind!=1 or size+32!=len(data) or core.fnv1_32(data[32:])!=checksum:
                    raise core.SaveError('Invalid embedded restart container')
            leaves.append(start)
    return sorted(leaves)


def clear_restart(f):
    starts=restart_leaves(f)  # Validate every record before changing any.
    # Most slots already hold the canonical zero-length blob. Rebuilding one
    # still reparses the entire save, so leave those exact bytes in place.
    starts=[start for start in starts if f.u32(start+4) != 0]
    result=core.SaveFile(f.payload)
    for start in reversed(starts):
        result=core.SaveFile(core.replace_content(result,start,bytes(4)))
    assert len(restart_leaves(result))==16
    return result.payload


def normalized_blocks(f):
    tree=f.tree()
    return {b.name:tree.copy_object(tree.node_at(b.start),0) for b in f.blocks}



# Part 2 title dates from the private timeline; Chapter 1/year from the native
# checkpoint. Cai Chapters 1–6 subsequently passed short-session game checks.
PART2_TESTED = frozenset(range(1, 7))
PART2_TESTED_BY_ROUTE = {route: PART2_TESTED for route in story.PREFIXES}
PART2_UPPER_MOVEMENT = core.id_hash("行動範囲制限_上層")
PART2_MIDDLE_MOVEMENT = core.id_hash("行動範囲制限_中層")
PART2_DATES = {1: (1, 1, 12, 0), 2: (2, 1, 12, 0), 3: (3, 1, 12, 0),
               4: (4, 3, 12, 0), 5: (4, 30, 9, 30), 6: (4, 30, 12, 0)}
PART3_DATES = {1: (1, 24, 8, 0), 2: (2, 1, 12, 0), 3: (2, 16, 12, 0),
               4: (3, 7, 12, 0), 5: (4, 6, 12, 0), 6: (5, 16, 12, 0)}


def chapters_for(route, part=1):
    if type(part) is not int or type(route) is not int:
        raise story.StoryError('Unsupported story route or part.')
    if part == 3 and route == 9:
        return tuple(ch for ch in story.PART3_CHAPTERS if ch != 1)
    if part == 2 and route in story.PREFIXES:
        return story.PART2_CHAPTERS
    if part == 1 and route in TARGETS:
        return TARGETS[route]
    raise story.StoryError('Unsupported story route or part.')


def target(chapter, route=4, part=1):
    if part == 3:
        story.sequence(chapter, route, part)
        if chapter == 1:
            raise story.StoryError('Part 3 Chapter 1 replay is unavailable. Start it through the Obelisk door instead.')
        return PART3_DATES[chapter]
    if part == 2:
        story.sequence(chapter, route, part)
        return PART2_DATES[chapter]
    if type(part) is not int or part != 1:
        raise story.StoryError('Unsupported story part.')
    if type(route) is not int or route not in TARGETS:
        raise story.StoryError('Story editing supports Leda, Cai, Dietrich and Theodora Part 1 only.')
    if type(chapter) is not int or chapter not in TARGETS[route]:
        if route == 2:
            raise story.StoryError('Choose a Dietrich Part 1 chapter from 3 to 12. Chapters 1 and 2 are unavailable because the Chapter 2 rescue cannot be progressed on replay.')
        if route == 1:
            raise story.StoryError('Choose a Cai Part 1 chapter from 1 to 12.')
        if route == 3:
            raise story.StoryError('Choose a Theodora Part 1 chapter from 1 to 12.')
        raise story.StoryError('Choose a Leda Part 1 chapter from 2 to 12. Chapter 1 is unavailable because its first objective cannot be progressed.')
    return {1: CAI_DATES, 2: DIETRICH_DATES, 3: THEODORA_DATES, 4: ENTRY_DATES}[route][chapter]


def validate(f):
    # Reject unsupported resume contexts before walking their variable records.
    # The Chapter 2 progression return has context 12 06 and a layout that the
    # generic object-tree decoder cannot traverse; it is still a valid game save.
    header = one_block(f, 'Header')
    mode = bytes(f.payload[header.start+20:header.start+22])
    if mode not in (b'\x12\x05', b'\x10\x0b'):
        raise story.StoryError('Story editing needs a supported free-time or chapter-start save. Battle and unknown resume states are read-only.')
    info = story.require_supported(f)
    resume = struct.unpack_from('<Q', f.payload, info.user+RESUME_OFFSET)[0]
    if (mode, resume) not in ((b'\x12\x05', FREE_TIME_ID), (b'\x10\x0b', CHECKPOINT_ID)):
        raise story.StoryError('Story editing needs a supported free-time or chapter-start save. Battle and unknown resume states are read-only.')
    schedule = one_block(f, 'GameSchedule')
    calendar = one_block(f, 'Calendar')
    if schedule.end-schedule.start != 24 or f.payload[schedule.start+4] != 1:
        raise story.StoryError('Unknown GameSchedule layout; no chapter changes allowed.')
    if calendar.end-calendar.start != 16 or f.payload[calendar.start+4] != 6:
        raise story.StoryError('Unknown Calendar layout; no chapter changes allowed.')
    clock = bytes(f.payload[schedule.start+5:schedule.start+12])
    if clock != bytes(f.payload[info.header+22:info.header+29]):
        raise story.StoryError('Header and schedule clocks disagree; no chapter changes allowed.')
    try:
        datetime(*struct.unpack('<H5B', clock))
    except ValueError as exc:
        raise story.StoryError('Invalid source calendar date; no chapter changes allowed.') from exc
    restart_leaves(f)  # Validate every cached blob before applying any change.
    return info


def edited(f, chapter):
    info = validate(f)
    date = target(chapter, info.route, info.part)
    if info.part == 3:
        return _edited_at_entry(f, chapter, 1454, date)
    if info.part == 2:
        p = _edited_at_entry(f, chapter, 1450, date)
        if chapter == 5:
            p = repair_part2_chapter5(core.SaveFile(p))
        if chapter == 6:
            p = repair_part2_chapter6(core.SaveFile(p))
        return p
    year = (THEODORA_YEARS[chapter] if info.route == 3 else
            ENTRY_YEARS[chapter] if info.route == 4 else 1449)
    p = _edited_at_entry(f, chapter, year, date)
    if info.route == 1 and chapter >= 3:
        p = facilities.edited(core.SaveFile(p), {facilities.SEWERS: True})
    if info.route == 2:
        p = story_prerequisites.edited(core.SaveFile(p), chapter)
    if info.route == 3:
        p = story_theodora_prerequisites.edited(core.SaveFile(p), chapter)
    return p


def _edited_at_entry(f, chapter, year, date):
    """Shared mechanics; guarded research probes may use non-production targets."""
    month, day, hour, minute = date
    info = validate(f)
    original = normalized_blocks(f)
    schedule, calendar = one_block(f, 'GameSchedule'), one_block(f, 'Calendar')
    clock = struct.pack('<H5B', year, month, day, hour, minute, 0)
    p = story.edited(f, chapter, route=info.route)
    p[info.header+20:info.header+22] = b'\x10\x0b'
    p[info.header+22:info.header+29] = clock
    p[schedule.start+5:schedule.end] = clock+bytes(12)
    p[calendar.start+5:calendar.end] = bytes(11)
    struct.pack_into('<Q', p, info.user+RESUME_OFFSET, CHECKPOINT_ID)
    p = clear_restart(core.SaveFile(p))
    result = core.SaveFile(p)
    check = validate(result)
    after = normalized_blocks(result)
    allowed = {'Header', 'GameUserData', 'GameSchedule', 'Calendar', 'GameRestartData'}
    if original.keys() != after.keys() or any(original[n] != after[n] for n in original.keys()-allowed):
        raise story.StoryError('An unrelated object changed; the chapter edit was refused.')
    user = bytearray(original['GameUserData'])
    user[9] = chapter
    struct.pack_into('<Q', user, 85, story.sequence(chapter, info.route, info.part))
    struct.pack_into('<Q', user, 4+RESUME_OFFSET, CHECKPOINT_ID)
    if bytes(user) != after['GameUserData'] or check.chapter != chapter:
        raise story.StoryError('Unexpected player or flag changes; the chapter edit was refused.')
    return p


def repair_part2_chapter5(f):
    """Shared A30 gate repair; all four routes reached the Chapter 5 battle."""
    info = validate(f)
    if info.route not in story.PREFIXES or (info.part, info.chapter) != (2, 5):
        raise story.StoryError('The temple-access repair requires Part 2 Chapter 5.')
    return facilities.edited(f, {PART2_UPPER_MOVEMENT: True})


def repair_part2_chapter6(f):
    """Clear only middle-city movement; Theodora's manual repair reached battle."""
    info = validate(f)
    if info.route not in story.PREFIXES or (info.part, info.chapter) != (2, 6):
        raise story.StoryError('The midtown-access repair requires Part 2 Chapter 6.')
    return facilities.edited(f, {PART2_MIDDLE_MOVEMENT: True})


def enter_part2(f):
    """Experimental direct entry; preserve Part 1 party, flags and world state.

    This deliberately tests whether chapter entry suffices without importing the
    native transition's flag changes. Native 1208 handoff/battle states remain
    unsupported. The caller must opt its container into part-summary syncing.
    """
    info = validate(f)
    if info.route not in story.PREFIXES or info.part != 1:
        raise story.StoryError('Start this experiment from a supported Part 1 free-time or chapter-start save.')
    original = normalized_blocks(f)
    p = bytearray(f.payload)
    for part_at, chapter_at, seq_at in ((info.header+13, info.header+14, info.header+45),
                                       (info.user+4, info.user+5, info.user+81)):
        p[part_at] = 2; p[chapter_at] = 1
        struct.pack_into('<Q', p, seq_at, story.sequence(1, info.route, 2))
    result = core.SaveFile(_edited_at_entry(core.SaveFile(p), 1, 1450, PART2_DATES[1]))
    after = normalized_blocks(result)
    allowed = {'Header','GameUserData','GameSchedule','Calendar','GameRestartData'}
    if original.keys() != after.keys() or any(original[n] != after[n] for n in original.keys()-allowed):
        raise story.StoryError('Unexpected changes during Part 2 entry; no changes applied.')
    expected = bytearray(original['GameUserData'])
    expected[8:10] = bytes((2, 1))
    struct.pack_into('<Q', expected, 85, story.sequence(1, info.route, 2))
    struct.pack_into('<Q', expected, 4+RESUME_OFFSET, CHECKPOINT_ID)
    if expected != after['GameUserData']:
        raise story.StoryError('Part 2 entry unexpectedly changed player data or flags.')
    return bytearray(result.payload)


def enter_cai_part2(f):
    """Keep historical Cai-only research probes bounded to their original route."""
    if validate(f).route != 1:
        raise story.StoryError('This historical probe requires Cai.')
    return enter_part2(f)


def repair_cai_part2_chapter5(f):
    """Keep the original Cai-only repair probe reproducible."""
    if validate(f).route != 1:
        raise story.StoryError('This historical probe requires Cai.')
    return repair_part2_chapter5(f)
