"""Experimental Leda Part 1 chapter entry; no prior-progression grants.

The sequence hashes extend the independently matching Chapter 1/2 checkpoint
suffix pattern. Chapter 9's earlier restoration loaded and progressed in game.
The remaining entries are inferred, despite all 12 chapters existing in data.
"""
from dataclasses import dataclass
import struct

import fefw_core as core

CHAPTERS = tuple(range(1, 13))
LEDA_PREFIX = 0xfde8dadc5dfc1118
ROUTES = {1: 'Cai', 2: 'Dietrich', 3: 'Theodora', 4: 'Leda', 9: 'Eshmel'}


class StoryError(core.SaveError):
    pass


def sequence(chapter):
    if type(chapter) is not int or chapter not in CHAPTERS:
        raise StoryError('Choose a Leda Part 1 chapter from 1 to 12.')
    value = LEDA_PREFIX
    for byte in f'{chapter}_1'.encode('ascii'):
        value = ((value * 0x100000001b3) & 0xffffffffffffffff) ^ byte
    return value


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
    tree = core.SaveTree(f.payload)
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


def check_outer(raw, info):
    """Chapter/sequence may lag unsaved edits; route and part must still agree."""
    if len(raw) < 81 or raw[36] != 15 or tuple(raw[40:42]) != (info.route, info.part):
        raise StoryError('The outer save summary disagrees with the live route/part.')


def edited(f, chapter):
    target = sequence(chapter)
    info = require_leda(f)  # Recheck at the mutation boundary, not just in the UI.
    p = bytearray(f.payload)
    p[info.header + 14] = p[info.user + 5] = chapter
    for at in (info.header + 45, info.user + 81):
        struct.pack_into('<Q', p, at, target)
    check = require_leda(core.SaveFile(p))
    if (check.chapter, check.sequence) != (chapter, target):
        raise StoryError('The chapter edit did not validate.')
    return p


def sync_outer_summary(payload, out):
    """Derive chapter, sequence, entry state and clock mirrors when serializing.

Only known, consistent Leda P1 layouts are eligible. Other routes/formats and
ambiguous files keep their original summary. No raw container state is changed
at edit time; the existing payload-only Undo stack remains authoritative.
"""
    try:
        info = require_leda(core.SaveFile(payload))
        check_outer(out, info)
    except (core.SaveError, IndexError, struct.error):
        return
    out[42] = info.chapter
    struct.pack_into('<Q', out, 73, info.sequence)
    out[48:57] = payload[info.header+20:info.header+29]
