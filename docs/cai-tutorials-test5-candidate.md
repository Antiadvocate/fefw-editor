# Cai/Tutorials Test 5 implementation evidence

The candidate adds Cai Part 1 Chapters 1, 5–8 and 10–12 to the existing selector,
retaining game-test labels for 2/3/9 and the conditional Chapter 4 Sewers result.
All Cai entries use year 1449; Chapter 1's January 24, 02:00 date comes from its
native checkpoint, while later dates match the private Cai timeline title rows.
Every supported Cai target >=3 enables the Sewers prerequisite atomically.

The full Tutorial and Tutorial_P0 inventory is 217 + 1 = 218 unique keys.
Exact group/child identities, title IDs and hashes are recorded; one key
contains a significant U+3000 space. Existing 115 labels are preserved. The
103 additions are provisional English translations, explicitly distinguished
in Tutorials and Flags. No localized game message bodies are copied.

Tutorials gains category, state and naming-evidence filters, Select shown,
per-row evidence and horizontal scrolling. Bulk edits can now remove the last
known tutorial and restore an empty recognized member. Unknown records and
raw wide encodings are preserved; unknown states refuse the complete batch.

The structural member is `e9bc5b65`. The usual anchored flag group is preferred;
the native Chapter 1 save has no free-time anchors and uses a separately
validated complete 13-member signature. This fallback identifies tutorial and
dialogue siblings only; general Functions edits still need their two anchors.
Missing/duplicate members, mismatched child identities and ambiguity are
rejected. The existing populated-list fallback remains for older supported
layouts; it cannot clear its last identifying anchors.

`research/cai_tutorial_test_kit.py` fingerprints three private sources before
building nine chapter cases and three tutorial-only cases. The native Chapter 1
checkpoint supplies C5-01, the original Chapter 2 Auto supplies C5-04, and the
passed Sewers arrival supplies the remaining cases. Every exported save is
reopened and checksum/summary checked; input bytes remain unchanged. Chapter
cases preserve tutorial lists. Tutorial cases restore their original list to
prove every unrelated normalized block matches.

Public synthetic tests, private table/return/candidate tests and live Tk
checks cover these boundaries. CI checks Linux and Windows on Python 3.10/3.12.
The delivered ZIP records actual verification results. Game acceptance of the
new targets and tutorial cases is still pending; follow the linked guide.

[Test guide](testing-cai-tutorials-test5.md)
