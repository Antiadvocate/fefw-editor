"""Leda Part 1 chapter entry, using the game-tested Test 3 D profile.

Leda Chapters 2–12 have short-session game evidence. Chapter 1 is unavailable:
its opening plays but its first objective cannot be progressed.
No private captures or GameData are required at runtime.
Cai Part 1 Chapters 2/9 passed short-session tests; Chapter 4 remains blocked.
"""
from datetime import datetime
import struct

import fefw_core as core
import story

CHAPTERS = tuple(range(2, 13))
TESTED = frozenset(CHAPTERS)
# Chapter 1's title inherits its date; use the captured natural checkpoint.
# Later chapters return to 1449, including when the source is Chapter 1.
ENTRY_YEARS = {chapter: 1444 if chapter == 1 else 1449 for chapter in range(1, 13)}
ENTRY_DATES = {1: (12, 1, 12, 0), 2: (1, 2, 12, 0), 3: (1, 20, 20, 0),
               4: (3, 1, 8, 0), 5: (4, 6, 12, 0), 6: (5, 8, 12, 0),
               7: (5, 28, 20, 0), 8: (6, 29, 11, 0), 9: (7, 10, 18, 0),
               10: (9, 28, 2, 0), 11: (10, 16, 12, 0), 12: (11, 7, 12, 0)}
CAI_DATES = {2: (1, 25, 11, 0), 4: (3, 1, 12, 0), 9: (9, 3, 12, 0)}
TARGETS = {4: CHAPTERS, 1: tuple(CAI_DATES)}
TESTED_BY_ROUTE = {4: TESTED, 1: frozenset((2, 9))}
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
    tree=core.SaveTree(f.payload);block=one_block(f,'GameRestartData')
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
    result=core.SaveFile(f.payload)
    for start in reversed(starts):
        result=core.SaveFile(core.replace_content(result,start,bytes(4)))
    assert len(restart_leaves(result))==16
    return result.payload


def normalized_blocks(f):
    tree=core.SaveTree(f.payload)
    return {b.name:tree.copy_object(tree.node_at(b.start),0) for b in f.blocks}



def target(chapter, route=4):
    if type(route) is not int or route not in TARGETS:
        raise story.StoryError('Story editing supports Leda and Cai Part 1 only.')
    if type(chapter) is not int or chapter not in TARGETS[route]:
        if route == 1:
            raise story.StoryError('Choose Cai Part 1 Chapter 2, 4 or 9. Other Cai targets are not yet available.')
        raise story.StoryError('Choose a Leda Part 1 chapter from 2 to 12. Chapter 1 is unavailable because its first objective cannot be progressed.')
    return (CAI_DATES if route == 1 else ENTRY_DATES)[chapter]


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
    date = target(chapter, info.route)
    return _edited_at_entry(f, chapter, ENTRY_YEARS[chapter], date)


def _edited_at_entry(f, chapter, year, date):
    """Shared mechanics; research alone may reproduce the failed Chapter 1 probe."""
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
    struct.pack_into('<Q', user, 85, story.sequence(chapter, info.route))
    struct.pack_into('<Q', user, 4+RESUME_OFFSET, CHECKPOINT_ID)
    if bytes(user) != after['GameUserData'] or check.chapter != chapter:
        raise story.StoryError('Unexpected player or flag changes; the chapter edit was refused.')
    return p
