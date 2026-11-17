"""Bounded Dietrich prerequisites supported by the player's Test 2 results.

These are exact chapter targets, not a blanket unlock of earlier progression.
Chapter 6 retains its intentional upper movement restriction. Chapter 2 has
no automatic repair: its native control passed, but replay repairs failed.
"""
import fefw_core as core
import facilities

PROGRESSION = 0x4ad575a2
UPPER = core.id_hash('行動範囲制限_上層')
LOWER = core.id_hash('行動範囲制限_下層')
SECRET = core.id_hash('使用許可_秘伝・風切投槍')
CHAPTER_EDITS = {
    5: {PROGRESSION: {UPPER: None}},
    6: {PROGRESSION: {LOWER: None}, facilities.GENERAL_MEMBER: {
        core.id_hash(k): 1 for k in ('機能開放_ダグシオン上層',
            '機能開放_ダグシオン下層', '機能開放_ヴァンダル商会')}},
    7: {PROGRESSION: {SECRET: 1}},
}


def member_map(f, member):
    """Read a direct flag-group member, including the native empty encoding."""
    tree, group, _ = facilities.flag_group(f)
    parent = tree.nodes[group]; table = f.ptr(parent.start)
    count = f.u32(parent.start) >> 24
    rows = [(f.u32(table+8*i), f.ptr(table+8*i+4)) for i in range(count)]
    if (table+8*count != parent.end or len({k for k,v in rows}) != count
            or len({v for k,v in rows}) != count
            or {v for k,v in rows} != {n.start for n in tree.nodes if n.parent == group}):
        raise core.SaveError('Unrecognised story flag group; no changes made.')
    hits = [at for key,at in rows if key == member]
    if len(hits) != 1:
        raise core.SaveError('Missing story prerequisite map; no changes made.')
    at = hits[0]; index = tree.node_at(at); node = tree.nodes[index]
    if node.struct or node.parent != group or any(n.parent == index for n in tree.nodes):
        raise core.SaveError('Unexpected story prerequisite structure.')
    maps = [m for m in core.flag_maps(f) if m.start == at]
    if not maps and bytes(f.payload[at+4:node.end]) == bytes(4):
        return core.FlagMap(-1, at, [])
    if (len(maps) != 1 or f.ptr(at) != node.end
            or len({v.hash for v in maps[0].flags}) != len(maps[0].flags)):
        raise core.SaveError('Invalid story prerequisite records.')
    return maps[0]


def edited(f, chapter):
    import story
    info = story.read(f)
    if (info.route, info.part) != (2, 1):
        raise core.SaveError('Dietrich prerequisites cannot change another route.')
    if type(chapter) is not int or chapter not in range(1, 13):
        raise core.SaveError('Unknown Dietrich chapter prerequisite target.')
    plans = []
    for member, changes in CHAPTER_EDITS.get(chapter, {}).items():
        fm = member_map(f, member); existing = {v.hash:v for v in fm.flags}
        effective = {}
        for h, value in changes.items():
            old = existing.get(h)
            if old and (old.wide or old.value not in (0, 1)):
                raise core.SaveError('Unknown story prerequisite value; no changes made.')
            if (old is not None if value is None else old is None or old.value != value):
                effective[h] = value
        if effective: plans.append((fm, effective))
    # Validate all maps before rebuilding; descending offsets retain addresses.
    result = core.SaveFile(f.payload)
    for fm, effective in sorted(plans, key=lambda p:p[0].start, reverse=True):
        result = core.SaveFile(facilities._edit_map(result, fm, effective))
    return bytearray(result.payload)
