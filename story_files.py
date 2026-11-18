"""Save-time chapter checkpoint writes; never called by Apply or Undo."""
from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

import fefw_core as core
import fefw_save as container
import story
import story_start


@dataclass(frozen=True)
class ChapterWrite:
    source: str
    target: str
    data: bytes
    previous: bytes | None


def path_key(path):
    return os.path.normcase(os.path.abspath(path))


def disk_bytes(path):
    p = Path(path)
    if p.is_symlink():
        raise core.SaveError(f'Chapter file is a symbolic link: {p.name}')
    try:
        return p.read_bytes()
    except FileNotFoundError:
        return None


def prepare(files, dirty):
    """Validate and serialize every requested write before any save is changed."""
    plans = {}
    targets = set()
    dirty_keys = {path_key(p) for p in dirty}
    for source in sorted(dirty):
        sv = files.get(source)
        request = getattr(sv, '_pending_story_chapter', None)
        if request is None:
            continue
        if not isinstance(request, story.ChapterFileRequest):
            raise core.SaveError('Unknown chapter-file request. Apply the chapter start again.')
        chapter = request.chapter
        f = core.SaveFile(sv.payload)
        info = story_start.validate(f)
        story.check_outer(sv.raw, info, allow_part_change=
                          getattr(sv, "_allow_part_transition", False))
        # Reject stale requests after a snapshot restore or unrelated story edit.
        if (info.route != request.route or info.part != request.part or info.chapter != chapter
                or bytes(story_start.edited(f, chapter)) != bytes(f.payload)):
            raise core.SaveError('The requested chapter file no longer matches a staged chapter start. Apply the chapter start again before saving.')
        target = str(Path(source).absolute().with_name(story.chapter_filename(info.route, chapter, info.part)))
        key = path_key(target)
        if key in targets or (key in dirty_keys and key != path_key(source)):
            raise core.SaveError(f'{Path(target).name} has competing unsaved changes. Save or discard that slot first.')
        targets.add(key)
        previous = disk_bytes(target)
        plans[source] = ChapterWrite(source, target, sv.to_bytes(), previous)
    return plans


def check_unchanged(plan):
    if disk_bytes(plan.target) != plan.previous:
        raise core.SaveError(f'{Path(plan.target).name} changed after the overwrite check. Save again to review the current file.')


def write(plan):
    """Back up the exact existing file before atomically replacing it."""
    check_unchanged(plan)
    if plan.previous is not None:
        container.write_backup(plan.target)  # Failure aborts replacement.
    fd, temporary = tempfile.mkstemp(prefix=Path(plan.target).name+'.', suffix='.tmp',
                                     dir=str(Path(plan.target).parent))
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(plan.data)
        check_unchanged(plan)
        os.replace(temporary, plan.target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def completed(app, sv):
    """Consume the request; history must never silently repeat an external write."""
    sv._pending_story_chapter = None
    if getattr(app, '_history_slot', None) is sv:
        for name in ('_undo_stack', '_redo_stack'):
            stack = getattr(app, name, [])
            stack[:] = [[(slot, payload, None if slot is sv else pending)
                         for slot, payload, pending in snapshot] for snapshot in stack]
