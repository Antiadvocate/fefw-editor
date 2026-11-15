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

GitHub Actions [run 43710564378](https://github.com/Destorino5/fefw-editor/actions/runs/43710564378)
passed on Linux and Windows with Python 3.10 and 3.12 for implementation/source
commit `052cd41dfd7e496e02ec63d12a2aa63c2d74eb54`. Each of the four jobs ran
41 public tests successfully and skipped the three private-fixture checks.
That exact source is in the delivered Test 1 ZIP, with an additional BUILD.txt.

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
Minimum-width behavior and in-game results were subsequently reported passed
by the player, as recorded below; they were not independently observed here.

## In-game acceptance: PASS on the reported setup

On 2026-11-15 the player reported **OPEN-01 & 02: Pass**,
**FT-01: See screenshots for in-game translations, otherwise pass**, and
**FT-02–08: Pass**, following [the testing guide](testing-fast-travel.md).
Evidence includes three side-by-side screenshots of the game Base Map menu
and editor, plus the private `Auto (FT-03)` and `Auto (FT-04)` files.

| Case | Scope | Result and evidence |
|---|---|---|
| OPEN-01 | Visible Open action, minimum width, chooser/cancel and Ctrl+O | PASS, player report |
| OPEN-02 | Unsaved-edit prompt and cancel/undo | PASS, player report; also independently smoke-tested |
| FT-01 | Baseline, searches, Japanese keys and names | Functionality PASS; eight English corrections supplied in screenshots and applied in current source |
| FT-02 | Port remove, undo/redo, save/reload | PASS, player report; also independently smoke-tested under the old Harbor label |
| FT-03 | Port removal in game and persistence | PASS, player report; supplied file independently contains no `1b5a4006` record |
| FT-04 | Port restoration, travel and persistence | PASS, player report; supplied file independently contains `1b5a4006 = 1` |
| FT-05 | Kalla's Temple removal/restoration, travel and persistence | PASS, player report; no separate case file supplied |
| FT-06 | Stables destination edits/travel with stable services still locked | PASS, player report; no separate case file supplied |
| FT-07 | No-op, mirroring guard and minimum-anchor refusal | PASS, player report |
| FT-08 | Tutorials, Blessings, world map, chapter/quests, existing boon and deed claims | PASS, player report; tutorial and blessing values also compared in both supplied files |

Both supplied files were read without modification and pass container checksum
verification. FT-03 has 15 of 16 known destinations: only Port is absent.
FT-04 has all 16 at value 1, matching B0's full destination mapping. Every
other known destination and all 14 unlisted records have B0's values in both
files. The full tutorial mapping, all seven gods' EXP and selection bytes,
and Divine Sand (100) match B0. `機能開放_厩舎` remains absent in both files,
as in B0. These are comparisons of the specified fields, not a claim that all
save bytes are identical after playing. Arrival at the correct location and
the broader FT-08 checks are supported by the player's report, not by those
field comparisons alone.

### Confirmed English labels

The screenshots show every destination in the catalogue. The following eight
provisional labels needed correction; all six temple names, Stables and Tavern
already matched. The full Japanese keys and hashes remain unchanged.

| Hash | Test 1 label | Confirmed in-game label |
|---|---|---|
| `5a48ce35` | Arena Entrance | Arena Plaza |
| `bb86129f` | Shopping Street | Shopping Arcade |
| `ad2b97e0` | Commercial District | City Streets |
| `387f1e5a` | Upper Approach | Upper Temple Row |
| `9b4262d7` | Lower Approach | Lower Temple Row |
| `90d7a0f8` | Affluent District | Entertainment District |
| `1b5a4006` | Harbor | Port |
| `e86370a7` | Slums | Lowtown |

Current source uses these names in Fast travel and Flags, removes the
provisional/translated and pending-test UI wording, and records per-entry
evidence in the catalogue. No locator, save parser or write behavior changed.
The original Test 1 ZIP remains unchanged as the exact tested artifact. No
repeat game acceptance run is required for these label/documentation updates.
The follow-up passed the public test suite (41 tests passed, three private
fixture tests skipped) and `git diff --check`. Both newly supplied private case
files were independently inspected as described above.

### Coverage limits

The reported test setup continues Leda Part I Chapter 9,
`fefw-recomp-0.1.5`, Bazzite 45 NVIDIA / Wayland, Ryzen 7 5800X3D / 32 GiB /
RTX 5080. Exact underlying game data and tester Python versions remain
unreported. The defined milestone acceptance cases are complete for this
setup. Isolated in-game edits/arrival/persistence were tested for Port,
Kalla's Temple and Stables; the other 13 entries were confirmed in the full
list and screenshots, with automated serialization checks for every entry.
This is not an isolated game test for each of those 13 entries. No conclusions
are drawn about other routes, hubs, sparse early saves or versions. No private
save or screenshot has been added to the public repository.
