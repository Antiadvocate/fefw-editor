"""Synthetic story payloads; no game data or personal saves in CI."""
from pathlib import Path
import struct
import tempfile
import unittest

import fefw_core as core
import fefw_save as container
import story
from test_tutorial_page import PageHarness


def fixture(route=4, part=1, chapter=2, *, padding=0, seq=0xb7b9cc2aad8d3152):
    p = bytearray(4)
    def leaf(body):
        at = len(p); p.extend(bytes(4) + body); p.extend(bytes(-len(p) % 4))
        struct.pack_into('<I', p, at, len(p) + 32); return at
    h = leaf(bytes(216)); p[h+8]=15; p[h+12:h+15]=bytes((route,part,chapter))
    struct.pack_into('<Q',p,h+45,seq)
    spare=leaf(b'\xfe' * (24+padding))
    u=len(p);p.extend(bytes(80));ud=u+4;p[ud]=23;p[ud+3:ud+6]=bytes((route,part,chapter))
    struct.pack_into('<III',p,ud+6,1523,6640,410)
    child=leaf(bytes([0])+struct.pack('<Q',seq)+bytes(3))
    extra=leaf(b'\xed'*20)
    t=len(p);p.extend(struct.pack('<IIII',0xabcdef01,child+32,0xabcdef02,extra+32))
    struct.pack_into('<I',p,u,(2<<24)|(t+32))
    t=len(p)
    for name,at in (('Header',h),('GameSound',spare),('GameUserData',u)):
        p.extend(struct.pack('<II',core.fnv1_32(name.encode()),at+32))
    struct.pack_into('<I',p,0,(3<<24)|(t+32))
    return core.SaveFile(p)


def raw_for(f):
    info=story.read(f);raw=bytearray(0x124)
    struct.pack_into('<I',raw,0,container.MAGIC);raw[36]=15
    raw[40:43]=bytes((info.route,info.part,info.chapter));struct.pack_into('<Q',raw,73,info.sequence)
    return raw


def box_for(f):
    box=container.SaveFile.__new__(container.SaveFile)
    box.raw=bytes(raw_for(f));box.zstd_offset=0x124;box.payload=bytearray(f.payload);box.path='synthetic'
    return box


class StoryTest(unittest.TestCase):
    def test_all_twelve_targets_change_only_chapter_and_live_sequence_and_noop(self):
        for padding in (0,20,84):
            f=fixture(padding=padding);before=bytes(f.payload);i=story.read(f)
            allowed={i.header+14,i.user+5,*range(i.header+45,i.header+53),*range(i.user+81,i.user+89)}
            for chapter in range(1,13):
                p=story.edited(f,chapter);g=core.SaveFile(p);j=story.require_leda(g)
                self.assertEqual((j.chapter,j.sequence),(chapter,story.sequence(chapter)))
                self.assertTrue({n for n,(a,b) in enumerate(zip(before,p)) if a!=b}<=allowed)
                self.assertEqual(len(p),len(before));self.assertEqual(story.edited(g,chapter),p)
            self.assertEqual(bytes(f.payload),before)
        # Independently captured checkpoint IDs / earlier accepted restoration.
        self.assertEqual(story.sequence(1),0xb7b6cc2aad8afbbd)
        self.assertEqual(story.sequence(2),0xb7b9cc2aad8d3152)
        self.assertEqual(story.sequence(9),0xb79bcc2aad7433e5)
        self.assertEqual(len({story.sequence(n) for n in story.CHAPTERS}),12)

    def test_non_leda_other_parts_and_invalid_chapters_refused_atomically(self):
        for route,part,chapter in ((1,1,2),(2,1,2),(3,1,2),(9,0,2),(4,2,2),(4,0,2),(42,1,2),(4,1,0),(4,1,13)):
            f=fixture(route,part,chapter);before=bytes(f.payload)
            with self.assertRaises(story.StoryError):story.edited(f,9)
            self.assertEqual(bytes(f.payload),before)
        for target in (0,13,-1,True,2.0,'2',None):
            with self.assertRaises(story.StoryError):story.edited(fixture(),target)

    def test_mismatched_missing_duplicate_and_unknown_structures_refused(self):
        def bad(offset,value):
            f=fixture();f.payload[offset]=value;return core.SaveFile(f.payload)
        f=fixture();i=story.read(f)
        for at,value in ((i.header+12,1),(i.user+4,2),(i.user+5,9),(i.user+81,0),
                         (i.user,22),(i.header+8,14),(i.user+80,1),(3,17)):
            g=bad(at,value);before=bytes(g.payload)
            with self.subTest(offset=at):
                with self.assertRaises(core.SaveError):story.edited(g,9)
                self.assertEqual(bytes(g.payload),before)
        for name in ('Header','GameUserData'):
            g=fixture();g.blocks.append(g.block(name))
            with self.assertRaises(story.StoryError):story.edited(g,9)
            g=fixture();g.blocks=[b for b in g.blocks if b.name!=name]
            with self.assertRaises(story.StoryError):story.edited(g,9)
        g=fixture();g.blocks[0].end-=4
        with self.assertRaises(story.StoryError):story.edited(g,9)
        raw=raw_for(f);raw[40]=1
        with self.assertRaises(story.StoryError):story.check_outer(raw,i)

    def test_serialized_summary_follows_edit_undo_and_redo_including_after_save(self):
        f=fixture();box=box_for(f);original=bytes(box.payload)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Auto';path.write_bytes(box.to_bytes());initial=path.read_bytes()
            box=container.SaveFile(str(path))
            box.payload=story.edited(core.SaveFile(box.payload),12);changed=bytes(box.payload)
            box.save()
            def check(chapter,seq):
                reopened=container.SaveFile(str(path));self.assertEqual(reopened.verify(),[])
                self.assertEqual(story.read(core.SaveFile(reopened.payload)).chapter,chapter)
                self.assertEqual(reopened.raw[42],chapter)
                self.assertEqual(struct.unpack_from('<Q',reopened.raw,73)[0],seq)
            check(12,story.sequence(12))
            box.payload=bytearray(original);box.save();check(2,story.sequence(2))
            box.payload=bytearray(changed);box.save();check(12,story.sequence(12))
            self.assertEqual(Path(str(path)+'.bak').read_bytes(),initial)
            self.assertTrue(Path(str(path)+'.bak1').exists());self.assertTrue(Path(str(path)+'.bak2').exists())
            # Header fields apart from chapter, sequence and checksum remain identical.
            actual=path.read_bytes();allowed={42,*range(73,81),*range(8,12)}
            self.assertTrue({n for n in range(256) if initial[n]!=actual[n]}<=allowed)

    def test_serializer_preserves_other_routes_unknown_and_ambiguous_summaries(self):
        for f in (fixture(1),fixture(3),fixture(4,2)):
            out=raw_for(f);out[42]=99;before=bytes(out);story.sync_outer_summary(f.payload,out)
            self.assertEqual(bytes(out),before)
        f=fixture();out=raw_for(f);out[40]=1;before=bytes(out)
        story.sync_outer_summary(f.payload,out);self.assertEqual(bytes(out),before)


class StoryHarness(PageHarness):
    def __init__(self,route=4):
        super().__init__();f=fixture(route);self.sv.payload=f.payload;self.sv.raw=bytes(raw_for(f))
        self.confirm=True;self.choice=9;self.confirmed=0;self.chosen=0
    def legacy_edit(self, chapter):
        # Exercise generic history with a previously staged Test 1 edit, not
        # the now-paused editor action.
        p=story.edited(core.SaveFile(self.sv.payload),chapter)
        if bytes(p)==bytes(self.sv.payload):return
        self.push_undo();self.sv.payload=p;self.sv._core_cache=None
        self._touch([self.sv]);self.refresh_after_core()
    def _confirm_story_warning(self):self.confirmed+=1;return self.confirm
    def _choose_story_chapter(self):self.chosen+=1;return self.choice


class StoryPageTest(unittest.TestCase):
    def test_cancel_each_dialog_does_not_edit_or_create_history(self):
        a=StoryHarness();original=bytes(a.sv.payload)
        a.confirm=False;a.open_story_progression();self.assertEqual(a.chosen,0)
        a.confirm=True;a.choice=None;a.open_story_progression()
        self.assertEqual(bytes(a.sv.payload),original);self.assertFalse(hasattr(a,'_undo_stack'))

    def test_applied_entry_undo_redo_and_noop(self):
        a=StoryHarness();original=bytes(a.sv.payload);a.core_of();a.legacy_edit(9)
        changed=bytes(a.sv.payload);self.assertNotEqual(original,changed)
        self.assertEqual(story.read(a.core_of()).chapter,9);self.assertEqual(a.dirty_slots,[a.sv])
        a.undo();self.assertEqual(bytes(a.sv.payload),original)
        a.redo();self.assertEqual(bytes(a.sv.payload),changed)
        n=len(a._undo_stack);a.legacy_edit(9);self.assertEqual(len(a._undo_stack),n)

    def test_cai_and_mirroring_refused_even_when_calling_edit_directly(self):
        for a in (StoryHarness(1),StoryHarness()):
            if story.read(a.core_of()).route==4:a.mirrored=True
            original=bytes(a.sv.payload);a.open_story_progression();a.apply_story_chapter(9)
            self.assertEqual(a.confirmed,0);self.assertEqual(bytes(a.sv.payload),original)
            self.assertFalse(hasattr(a,'_undo_stack'))

    def test_route_is_rechecked_after_warning(self):
        a=StoryHarness();replacement=fixture(1)
        def confirm():a.sv.payload=replacement.payload;a.sv.raw=bytes(raw_for(replacement));return True
        a._confirm_story_warning=confirm;a.open_story_progression()
        self.assertEqual(a.chosen,0);self.assertEqual(story.read(a.core_of()).route,1)
        self.assertFalse(hasattr(a,'_undo_stack'))

    def test_undo_and_redo_never_cross_loaded_slots_or_reloaded_objects(self):
        a=StoryHarness();leda=a.sv;original=bytes(leda.payload)
        a.legacy_edit(9);changed=bytes(leda.payload)
        cai=StoryHarness(1).sv;cai_before=bytes(cai.payload)
        a.sv=cai;a.undo();a.redo()
        self.assertEqual(bytes(cai.payload),cai_before)
        self.assertEqual(bytes(leda.payload),changed)
        a.sv=leda;a.undo();self.assertEqual(bytes(leda.payload),original)
        a.sv=cai;a.redo();self.assertEqual(bytes(cai.payload),cai_before)
        a.sv=leda;a.redo();self.assertEqual(bytes(leda.payload),changed)
        # Reloading the same path creates a new SaveFile; stale history cannot
        # overwrite a newly loaded game save even when the filename matches.
        a.sv=StoryHarness().sv;a.sv.path=leda.path;before=bytes(a.sv.payload)
        a.undo();a.redo();self.assertEqual(bytes(a.sv.payload),before)

    def test_new_edit_in_another_slot_starts_its_own_history(self):
        a=StoryHarness();a.legacy_edit(9)
        other=StoryHarness().sv;a.sv=other;before=bytes(other.payload)
        a.legacy_edit(12);self.assertEqual(len(a._undo_stack),1)
        a.undo();self.assertEqual(bytes(other.payload),before)
        a.undo();self.assertEqual(bytes(other.payload),before)

    def test_failed_general_writer_is_paused_and_obelisk_warning_precedes_backup(self):
        import story_page
        a=StoryHarness();before=bytes(a.sv.payload)
        a.apply_story_chapter(9);a.apply_story_chapter(1)
        self.assertEqual(bytes(a.sv.payload),before)
        self.assertFalse(hasattr(a,'_undo_stack'))
        self.assertIn('paused',a.messages[-1][0])
        self.assertEqual(story_page.WARNING_POINTS[-2],
            'Skipping chapters will lock them out of being present in the Obelisk Chamber as this relies on chapter save files.')
        self.assertIn('Back up',story_page.WARNING_POINTS[-1])
