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
    return facilities.locate_member(f, member)


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
