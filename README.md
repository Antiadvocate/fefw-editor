# Fortune's Weave Save Editor

A save editor for **Fire Emblem: Fortune's Weave** saves made by the Eden
Switch emulator. It edits your playthrough (units, items, convoy, gold, skills,
flags) and leaves the game itself alone. Plain Python + Tkinter, one extra
library, or a ready-made Windows `.exe`.

> **Unofficial and reverse-engineered.** Close the game before saving and keep
> your own backup. The first save next to each slot also keeps the untouched
> original as `<slot>.bak`.

![Units page](docs/units.png)

## What you can edit

| Page | Tab | What |
|---|---|---|
| **Units** | Stats | Level, EXP, max HP, and the points each of the nine stats has gained from level-ups (see *Stats* below) |
| | Arts & skills | All six skill lists in the unit's record (equipped arts, equipped skills, arts known, everything learned…), by name, with add / remove |
| | Inventory | Swap, add or remove a carried item, picked from a searchable catalogue. Known spells are listed separately |
| | Class | Pick any class the game knows. It's added to the unit's own class list, the way the game does it |
| **Convoy** | | Everything in storage, materials included: add a stack, stock every material at once, swap the item in any row, change its quantity, remove a row, and repair a list damaged by older versions |
| **Gold** | | Set gold |
| **Player** | | Gold, renown exp and Karma Shards; difficulty, mode and playthrough number (written into every slot, since they belong to the run) |
| **Classes** | | A unit's whole class list (set the current class, add, swap or remove one, set its exp) and its weapon masteries with their rank (E … S+) and exp — a range of masteries can be given the same exp at once |
| **Supports** | | Every character's support partners with the **points** this save holds for the pair, the highest rank the game defines, and which conversations this save has recorded. Set the points (0 … 3200) and the game works the level out from them. **Record conversation as seen** writes that conversation's flag |
| **Mounts** | | The battalion and mount each unit carries, chosen from the save's pool |
| **Flags** | | Every named variable the save stores: support conversations, recruited / met, achievements, feature and class unlocks. Search, filter, set, add, remove |

Units can also be **copied in** from another slot or **removed**. Every edit can
be undone (Ctrl+Z / Ctrl+Y), and **Snapshot** / **Restore…** keep copies of the
whole save folder.

### Stats

The nine stored numbers are what a unit has **gained from level-ups**. The game
adds the class and personal bases (and stat-up items) on top, so the editor's
numbers are lower than the unit screen; raising one raises the in-game stat by
the same amount. Max HP is stored separately and always equals a fixed base
plus the HP gained, so changing HP gained moves max HP with it.

### Not supported (yet)


* **Total stats and stat-up item bonuses.** See *Stats* above.
* **Movement.** Units have their own movement values; where they're stored isn't
  known yet.
* **Weapon-rank rewards and skill effects.** Raising a rank only changes the
  letter, and adding a skill doesn't grant an effect the class or level wouldn't
  allow. Skills and arts the game hands out when a rank is reached in play are
  not added.

If you know where any of these live, contributions are welcome.

## Download

Get the latest build from the
[**Releases page**](https://github.com/Antiadvocate/fefw-editor/releases/latest):

* **Windows:** `FEFW-Save-Editor-<version>-windows.zip`. Unzip it anywhere you
  can write to and run `FEFW Save Editor.exe`; no Python needed. The exe isn't
  code-signed, so SmartScreen may ask you to click *More info → Run anyway*.
* **Anything else:** `…-source.zip`, then see *Running from source*.

## Running from source

```
pip install -r requirements.txt
python editor.py
```

or double-click **FEFW Save Editor.bat** on Windows. Python 3.10+. You can also
pass a save folder (or any slot file in it): `python editor.py "C:\path\to\save"`.

## Finding your save

```
%APPDATA%\eden\nand\user\save\<play-uid>\<account>\04007EF01F8AE000\000\
```

The editor finds this on its own and remembers the last folder you opened.
Otherwise use **Open folder…** and pick any slot file inside it.

## How saving works

* **The slots.** `Auto` is your latest save on whichever lord's route you last
  played, and it opens first. `Route_<lord>` (e.g. `Route_Ism`) holds that
  lord's route while you play someone else. `Chapter_<lord>_<part>_<chapter>`
  are chapter checkpoints, the points the game's "go back in time" feature
  returns to. `Part_<lord>_<part>` are part checkpoints. `Global` holds settings
  only. The slot list shows the lord, part and chapter each slot was saved in
  (e.g. `★ Auto · Theodora P1 Ch12`), read from the save itself; ★ marks `Auto`.
* **Edit `Auto`.** It's the save the game continues from, so editing it alone is
  enough.
* **Only the live data is changed.** `Auto` also carries its own copies of
  earlier points (the chapter start and, mid-battle, older states). Edits go to
  the live unit, convoy and gold; those copies keep their values, so rewinding
  still takes you back to what was really there. Run settings (difficulty, mode,
  playthrough number) are the exception: they apply to the whole run and are
  written into every copy.
* **"Also edit this route's other saves"** (off by default) also writes each edit
  into the same route's other live saves, e.g. that lord's `Route_*`. Another
  lord's route and every `Chapter_*` checkpoint are never touched. Open a
  checkpoint to edit it on its own.
* **Nothing is written until you press Save** (Ctrl+S). Slots with unsaved
  edits get a ● in the slot list, and quitting with unsaved edits asks first.
* **Reload (F5)** re-reads every slot from disk. When you switch back to the
  editor, a slot the game saved since is re-read on its own if you haven't
  edited it; if you have, Save warns you before overwriting the game's newer
  save.
* **Snapshots** are stored in a `_snapshots` folder next to your slots.

Lists grow and shrink safely: the save is a tree of records that point at each
other, and when a list changes size every pointer after it is rewritten and the
result is read back before anything is written.

![Convoy page](docs/convoy.png)

## The convoy

The convoy is a fixed row of 1329 slots, one per item: each item has its own
slot, and a stack sitting in another item's slot is ignored by the game.
**Add item…** puts a stack in the item's own slot (adding to what is there) and
**Remove** empties a slot, so the list always keeps its 1329 slots.

**All materials…** asks for one quantity and stocks all 128 forging and cooking
materials (ores, meat, fish, plants, leaves, manure) at it, each in its own
slot. Undo takes it back.

**Fixing 1.3.1.** Version 1.3.1's Add item… and All materials… put stacks in the
first empty slot, so the game never showed them. Running All materials… again
moves stray materials home, and adding an item again moves its stray copies
into its own slot.

**Damaged lists.** Versions before 1.2 did "Add" by writing an item over empty
slots, which knocked the rest of the list out of line so the game couldn't read
it (materials stored after that point seemed to vanish). The Convoy page detects
such a list and offers **Repair convoy**: it rebuilds a clean list with every
item it can still find. Undo works, and the original stays in the slot's `.bak`.

## Finding items and skills

The catalogues search English name, Japanese name and id as you type; every word
must match, so `silver bow` or `+3 sword` narrow it down. The item catalogue has
a **Type** filter (Sword, Lance, Tome, Accessory…), and forged copies show their
level (`Silver Axe +2`) even where the game's English text leaves it out. When
you pick an inventory slot, only items of the same kind are offered; tick *Allow
any item type* to override. The skill picker lists skills with an English name
first.

**Icons:** items get a coloured dot by type and units an initials badge. Drop
PNGs into `icons/items/` and `icons/units/` to use real images; see
[icons/README.md](icons/README.md).

![Arts & skills tab](docs/skills.png)

## Keyboard

| Key | Does |
|---|---|
| Ctrl+S | Save every changed slot |
| Ctrl+Z / Ctrl+Y | Undo / redo |
| Ctrl+O | Open a save folder |
| Ctrl+F | Jump to the search box on the current page |
| Ctrl+A | Select every row in the table you last clicked |
| Shift+click / Shift+drag | Select a range of rows (convoy, classes, masteries, flags…) |
| F5 | Reload every slot from disk (asks first if you have unsaved edits) |
| Enter / double-click | Use the selected catalogue item |

## Known limits

* Changing a class writes the class id and the unit's class list; usable weapons
  and class skills that come with a class are not recalculated.
* EXP is a running total (`(level - 1) × 100 + EXP into the level`); the editor
  shows and writes the part inside the level, 0–99.
* Renown is stored as exp. Which level that is comes from the game's own
  tables, so the editor shows exp, not a level.
* A flag whose name isn't in the game's data files shows as `unknown 0x…`. It's a
  real flag that nothing in the data names (roughly 40% of a mid-game save's
  flags resolve).
* Enemy and NPC records can be viewed but not edited; their layout is only partly
  known.
* Built and tested against saves from one game version. Another version may need
  the name tables rebuilt; unknown ids then show as `unknown <hash>`.

## Files

```
editor.py            the GUI
editor_advanced.py   Arts & skills, Player, Classes, Supports, Flags and Mounts pages
ui_util.py           table helpers: Ctrl+A and Shift+drag range selection
fefw_core.py         the save's record tree: blocks, units, resizing edits, convoy, mounts, flags
fefw_layer.py        what the GUI uses: units, items, skills, convoy and gold through fefw_core
fefw_save.py         save container (decompress, checksums, write), ids and labels, small CLI
supports.py          support pair chart, conversation-flag and support-point lookup
unit_ids.json        person id -> name
item_ids.json        item id   -> Japanese + English name
job_ids.json         class id  -> Japanese + English name
skill_ids.json       skill id  -> Japanese + English name
supports.json        support pair -> highest rank and its conversation flags
support_points.json  support pair hash -> the two characters it joins (2628 pairs)
flag_names.json      flag id   -> readable name
build_skill_ids.py   rebuilds skill_ids.json from a romfs dump
build_item_names.py  puts the game's official English item names into item_ids.json
build_unit_names.py  English names for generic units, enemies and NPCs in unit_ids.json
msbt.py              reads the game's message files (used by the build scripts)
build_flag_names.py  rebuilds flag_names.json from a romfs dump
icons/               optional item / unit images
requirements.txt     zstandard
FEFW Save Editor.bat launcher (source install)
.github/workflows/   release build
```

`editor_settings.json` (theme, last folder, options) is created next to the
editor, or next to the `.exe`, on first use.

### Rebuilding the name tables

The `.json` name tables come from the game's own data. To rebuild them for a
different game version, point the scripts at a romfs dump of your own copy of
the game:

```
python build_item_names.py <romfs folder>
python build_unit_names.py <romfs folder>
python build_skill_ids.py <romfs folder>
python build_flag_names.py <romfs folder>/GameData
```

`build_item_names.py` replaces the English item names (until now translated
from the Japanese ids, e.g. "Augus' teff") with the game's own English text
("Orgus Coffee"), matched through the game's message files. Items the game's
text never names (cut content, cutscene props) get hand translations.
`build_unit_names.py` names the generic soldiers, enemies and NPCs whose ids are
Japanese (`EN_女斧盗賊2` → "Axe Thief (female, 2)") from the class, people and
place names in the same files.

## Making a release

1. Bump `__version__` in `editor.py` (e.g. `"1.2.1"`) and merge to `main`.
2. Actions → **Release** → *Run workflow*, and enter the matching tag
   (`v1.2.1`). Pushing that tag works too.

The workflow ([.github/workflows/release.yml](.github/workflows/release.yml))
checks the tag matches `__version__`, builds the Windows `.exe` with
PyInstaller, zips it with the README and the `icons/` folder, adds a source zip
and publishes the release.

## Disclaimer

No warranty. Editing saves can corrupt them, and this was built by studying a
handful of save files; behaviour may differ on other game versions. Keep your
own backups.
