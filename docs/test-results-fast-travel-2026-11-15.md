# Milestone 3 validation record — 2026-11-15

Candidate: **FEFW-Fast-Travel-Test-1**, branch `feature/fast-travel`.
The archive's `BUILD.txt` identifies the source commit and CI run. This is a
source candidate; no new packaged executable has been produced or tested.

## Automated checks

On Linux / Python 3.12.14:

```sh
FEFW_TEST_SAVE='/private/path/to/Auto' python -m unittest discover -s tests -v
```

**44 tests passed**, including three opt-in private-save tests. Without the
private fixture, **41 pass and three skip**. Compile checks and
`git diff --check` pass. Public fixtures contain only synthetic payloads.

New coverage includes exact scoped names and hashes; conflicting label
identities; shifted/reordered lists; rejection of unscoped lookalikes, duplicate
keys, ambiguous lists, unexpected hierarchy and too few identifying entries;
atomic invalid/unknown-state requests; no-op identity; preservation of wide
record encodings and all other list records. The page harness exercises the
real edit/undo/cache machinery, including undo/redo, mirroring refusal,
no-selection and no-op handling.

The read-only private B0 fixture is used to remove and restore each of the 16
destinations independently, with serialization and reload after every step.
All 32 edited files pass container checksum verification and retain the expected
availability. All other list records retain exact bytes. Before serialization,
all payload content outside the target list compares equal after normalizing
relocatable pointer targets. Serialization refreshes embedded checksums after
relocation; the reopened payload matches the serialized payload exactly. The
source file remains unchanged. Existing Tutorials and all-seven-god Blessings
regressions also pass.

The initial synthetic fixture assumed the list was a direct GameUserData
child. The real-save check rejected that assumption: the list lives inside a
struct flag group directly below GameUserData. The locator and fixtures now
require that observed hierarchy, and a regression rejects a map outside it.
No enumerated map index or absolute offset is used.

## Native GUI smoke check

The actual Tk editor was launched on the test desktop with Python 3.12 / Tk 9
and a disposable B0 copy. The checked behavior includes:

* Open is visible in the top action bar; the slot selector has its own row.
* Open invokes the save-file chooser, cancel retains the loaded save, Ctrl+O
  invokes the same chooser, and selecting Auto reloads that folder/slot.
* The Fast travel tab displays 16 available destinations and 14 other preserved
  list records; searching Harbor shows the matching hash and state.
* Removing Harbor produces Absent / 15 of 16 and an unsaved-change indicator.
* Clicking Open with unsaved edits shows the save/discard/cancel prompt.
  Cancel keeps the edited save. Undo restores Available / 16; redo removes it.
* Save and Reload retain Harbor's absence; an independent read of that GUI
  output also verifies its checksums and missing destination record.
* Make available restores Harbor. The GUI-saved restored copy has the same
  destination mapping, tutorial mapping, blessing EXP/selection and Divine Sand
  as B0, independently checked from disk.

The desktop's font/locale setup renders Japanese and some existing non-ASCII
punctuation incorrectly, as in the preceding milestone's smoke check. Source
strings are UTF-8 and the tester's Bazzite screenshots rendered the earlier
Japanese keys correctly. FT-01 checks these new keys on that system.
Minimum-width behavior and in-game results remain user acceptance checks.

## In-game acceptance: pending

The earlier restored full destination list was player-confirmed. That result
does not substitute for isolated tests of this new interface, removal behavior,
travel arrival or post-game-save persistence. See
[OPEN-01–02 and FT-01–08](testing-fast-travel.md). English destination labels
are provisional translations until the in-game wording is checked.

The intended test setup continues the reported Leda Part I Chapter 9,
`fefw-recomp-0.1.5`, Bazzite 45 NVIDIA / Wayland, Ryzen 7 5800X3D / 32 GiB /
RTX 5080 environment. No conclusions are drawn about other routes, hubs,
sparse early saves or versions. No private save or screenshot has been added
to the public repository.
