"""Live story validation for Parts 1/2 and provisional Eshmel Part 3.

Production chapter-entry targets and acceptance live in story_start. The low-level
sequence writer retains Chapter 1 for reproducing historical failed probes.
"""
from dataclasses import dataclass
import struct

import fefw_core as core

CHAPTERS = tuple(range(1, 13))
LEDA_PREFIX = 0xfde8dadc5dfc1118
CAI_PREFIX = 0xeab884585a706f5d
DIETRICH_PREFIX = 0x13dfaa82ebb06dc7
THEODORA_PREFIX = 0xa0f55a5342799b29
PREFIXES = {4: LEDA_PREFIX, 1: CAI_PREFIX, 2: DIETRICH_PREFIX, 3: THEODORA_PREFIX}
FILE_CODES = {4: 'Led', 1: 'Kai', 2: 'Dit', 3: 'Seo'}
FILE_CODES[9] = 'Ism'
ROUTES = {1: 'Cai', 2: 'Dietrich', 3: 'Theodora', 4: 'Leda', 9: 'Eshmel'}


class StoryError(core.SaveError):
    pass


# Shared Timeline_Part2 (戦争篇); target IDs captured/tested on Cai. Reuse for
# other routes is inferred until their game tests pass; route identity is retained.
PART2_PREFIX = 0x6462d9c33a114480
PART2_CHAPTERS = tuple(range(1, 7))
PART3_PREFIX = 0x93fa44edcc987313
PART3_CHAPTERS = tuple(range(1, 7))


def sequence(chapter, route=4, part=1):
    if type(part) is not int or part not in (1, 2, 3):
        raise StoryError('Unsupported story part.')
    if part == 3:
        if type(route) is not int or route != 9 or type(chapter) is not int or chapter not in PART3_CHAPTERS:
            raise StoryError('Part 3 chapter editing is only available for Eshmel, chapters 1–6.')
        value = PART3_PREFIX
        for byte in f'{chapter}_1'.encode('ascii'):
            value = ((value * 0x100000001b3) & 0xffffffffffffffff) ^ byte
        return value
    if part == 2:
        if type(route) is not int or route not in PREFIXES or type(chapter) is not int or chapter not in PART2_CHAPTERS:
            raise StoryError('Provisional Part 2 editing supports the four main routes, chapters 1–6 only.')
        value = PART2_PREFIX
        for byte in f'{chapter}_1'.encode('ascii'):
            value = ((value * 0x100000001b3) & 0xffffffffffffffff) ^ byte
        return value
    if type(chapter) is not int or chapter not in CHAPTERS:
        raise StoryError('Choose a Part 1 chapter from 1 to 12.')
    if type(route) is not int or route not in PREFIXES:
        raise StoryError('Story editing supports Leda, Cai, Dietrich and Theodora Part 1 only.')
    value = PREFIXES[route]
    for byte in f'{chapter}_1'.encode('ascii'):
        value = ((value * 0x100000001b3) & 0xffffffffffffffff) ^ byte
    return value


@dataclass(frozen=True)
class ChapterFileRequest:
    route: int
    chapter: int
    part: int = 1


def chapter_filename(route, chapter, part=1):
    sequence(chapter, route, part)  # Validate before constructing a filename.
    return f'Chapter_{FILE_CODES[route]}_{part}_{chapter}'


@dataclass(frozen=True)
class Progress:
    route: int
    part: int
    chapter: int
    sequence: int
    header: int
    user: int

    @property
    def label(self):
        return f'{ROUTES.get(self.route, "Unknown route " + str(self.route))} · Part {self.part} · Chapter {self.chapter}'


def read(f):
    """Require known, agreeing live fields; never scan or rewrite snapshots."""
    headers = [b for b in f.blocks if b.name == 'Header']
    users = [b for b in f.blocks if b.name == 'GameUserData']
    if len(headers) != 1 or len(users) != 1:
        raise StoryError('Cannot identify one live Header and GameUserData.')
    h, u = headers[0], users[0]
    ud = u.start + 4
    if h.end - h.start != 220 or f.payload[h.start + 8] != 15 or core.user_data(f) != ud:
        raise StoryError('Unknown story field layout; no changes allowed.')
    try:
        tree = f.tree()
    except RecursionError as exc:
        raise StoryError('Unsupported story object tree; no changes allowed.') from exc
    parent = tree.node_at(u.start)
    children = [n for n in tree.nodes if n.parent == parent]
    # In GameUserData v23 the current sequence is a 16-byte child object at
    # body+76, version 0, with its u64 at child+5. Verify that object rather
    # than assuming body+81 is an ordinary scalar in every save.
    sequence_nodes = [n for n in children if n.start == ud + 76]
    if (len(sequence_nodes) != 1 or sequence_nodes[0].struct
            or sequence_nodes[0].end != ud + 92 or f.payload[ud + 80] != 0
            or min(n.start for n in children) != ud + 76):
        raise StoryError('Unknown live story-sequence object; no changes allowed.')
    header_route = tuple(f.payload[h.start + 12:h.start + 15])
    user_route = tuple(f.payload[ud + 3:ud + 6])
    if header_route != user_route:
        raise StoryError('Header and live route/part/chapter disagree; no changes allowed.')
    a = struct.unpack_from('<Q', f.payload, h.start + 45)[0]
    b = struct.unpack_from('<Q', f.payload, ud + 81)[0]
    if a == 0 or a != b:
        raise StoryError('Header and live story sequences are missing or disagree.')
    return Progress(*user_route, a, h.start, ud)


def require_leda(f):
    info = read(f)
    if (info.route, info.part) != (4, 1):
        raise StoryError(f'{info.label}. Story editing is only available for Leda Part 1 saves.')
    if info.chapter not in CHAPTERS:
        raise StoryError('This Leda Part 1 chapter is outside the supported range (1–12).')
    return info


def require_supported(f):
    info = read(f)
    if info.route == 9 and info.part == 3 and info.chapter in PART3_CHAPTERS:
        return info
    if info.route in PREFIXES and info.part == 2 and info.chapter in PART2_CHAPTERS:
        return info
    if info.route not in PREFIXES or info.part != 1 or info.chapter not in CHAPTERS:
        raise StoryError(f'{info.label}. Story editing supports the four Part 1/2 routes and Eshmel Part 3 chapters 1–6.')
    return info


def check_outer(raw, info, *, allow_part_change=False):
    """Require matching route/part, except an explicitly staged same-route Part 1↔2 edit.

    The opt-in belongs to the selected container session and permits Undo after
    saving. Ordinary opens and unrelated saves still require exact agreement.
    """
    eligible_change = (allow_part_change is True and len(raw) >= 81
                       and raw[40] == info.route and info.route in PREFIXES
                       and raw[41] in (1, 2) and info.part in (1, 2))
    if len(raw) < 81 or raw[36] != 15 or (tuple(raw[40:42]) != (info.route, info.part) and not eligible_change):
        raise StoryError('The outer save summary disagrees with the live route/part.')


def edited(f, chapter, *, route=4):
    info = require_supported(f)
    target = sequence(chapter, route, info.part)
    if info.route != route:
        raise StoryError('The requested story route does not match the save; route conversion is not supported.')
    p = bytearray(f.payload)
    p[info.header + 14] = p[info.user + 5] = chapter
    for at in (info.header + 45, info.user + 81):
        struct.pack_into('<Q', p, at, target)
    check = require_supported(core.SaveFile(p))
    if (check.chapter, check.sequence) != (chapter, target):
        raise StoryError('The chapter edit did not validate.')
    return p


def sync_outer_summary(payload, out, *, allow_part_change=False):
    """Derive chapter, sequence, entry state and clock mirrors when serializing.

Only known, consistent supported story layouts are eligible. Other routes/formats and
ambiguous files keep their original summary. No raw container state is changed
at edit time; the payload in Undo history remains authoritative.
"""
    try:
        info = require_supported(core.SaveFile(payload))
        check_outer(out, info, allow_part_change=allow_part_change)
    except (core.SaveError, IndexError, struct.error):
        return
    out[41] = info.part
    out[42] = info.chapter
    struct.pack_into('<Q', out, 73, info.sequence)
    out[48:57] = payload[info.header+20:info.header+29]
