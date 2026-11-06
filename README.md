# Fortune's Weave Save Editor

A save editor for **Fire Emblem: Fortune's Weave** saves created by the
Eden / eglantine Switch emulator. Plain Python + Tkinter, one extra library.

> **Unofficial and reverse-engineered.** The first save next to each slot keeps
> the untouched original as `<slot>.bak` — but keep your own backup too.

![Units page](docs/units.png)

## What you can edit

| Page | Tab | What |
|---|---|---|
| **Units** | Stats | Level, EXP into the level, current HP and the points each of the nine stats has gained from level-ups (see below) |
| | Inventory | Swap, add or remove a carried item, picked from a searchable catalogue |
| | Arts & skills | The record's skill lists - equipped arts, equipped skills and everything learned - each with a name (English where the game has one) and add / remove |
| | Class | Pick any class the game knows (searchable, English + internal name). The class is added to the unit's own class list, the way the game does it |
| **Convoy** | | Everything in storage, materials included: add an item, swap the item in any row, change its quantity, clear a row |
| **Gold** | | Set gold. Found automatically in Theodora-route saves; other slots locate it once by the amount the game shows |
| **Player** | | Gold, **Renown exp**, **Karma Shards**, difficulty / mode and the playthrough number, written into every copy the save keeps |
| **Classes** | | A unit's whole class list (value + flags per class, ● = the current one): set the current class, add, swap or remove a class — and the **weapon masteries** with their rank letters (E…S+) and exp, which can be added, removed, or set to a rank |
| **Supports** | | Every support pair the game data defines, its highest rank and which conversations this save records — **Record conversation as seen** (C / B / A) writes that conversation's flag |
| **Mounts** | | The battalion (and mount) each unit carries, chosen from the save's pool |
| **Flags** | | Every named variable the save stores: 支援会話_* (support conversations), 加入_* (recruited), 面識_* (met), 実績_* (achievements), 機能開放_* (unlocks), 兵種解放_* (class unlocks). Search, filter, set a value, add, remove |

Records live in a tree of objects whose pointers are offsets into the save, and
the editor edits through that tree (`fefw_core.py`): when a list grows or
shrinks, every pointer after it is rewritten and the result is read back before
anything is written. That is what makes adding a class, a mastery or a flag
safe.

### What it doesn't do (yet)

This edits the parts of the save that have been mapped, not the whole game. Not
supported:

* **Total stats.** The nine stored numbers are what a unit gained from level-ups;
  the game adds class and personal bases (and any stat-up items) on top. So the
  editor's numbers are lower than the unit screen, and raising one raises the
  in-game stat by the same amount. Stat-up item bonuses aren't located yet.
* **Movement.** Units have their own movement values. Where they're stored isn't
  known yet.
* **Weapon-rank rewards.** Raising a rank only changes the letter; skills and
  combat arts granted on reaching a rank in play are not added.
* **Skill effects.** The lists are editable, but what a skill does comes from the
  game data - adding one doesn't grant its effect if the class or level
  requirement isn't met.
* **Support Lv and points.** They are not a plain value anywhere in the save.
  What can be written is the `支援会話_<A>_<B>_<rank>` flag — one per
  conversation, the same flag the game sets when the conversation is seen — so a
  support can be opened up to A; the bar itself stays with the game.
* **Mounts and battalions.** The lists parse and their records are understood
  (`SaveStable` in `fefw_core.py`), but there is no page for them yet.

If you know where any of these live (offsets, a cheat table, the game's data
files), contributions are welcome.

## Download

Grab the latest build from the
[**Releases page**](https://github.com/Antiadvocate/fefw-editor/releases/latest):

* **Windows:** `FEFW-Save-Editor-<version>-windows.zip` — unzip it anywhere you
  can write to and run `FEFW Save Editor.exe`. No Python needed. The exe isn't
  code-signed, so SmartScreen may ask you to click *More info → Run anyway*.
* **Anything else:** `…-source.zip`, then follow *Running from source* below.

## Running from source

```
pip install -r requirements.txt
python editor.py
```

or double-click **FEFW Save Editor.bat** on Windows. Python 3.10+.

You can also pass a folder (or any slot file) on the command line:
`python editor.py "C:\path\to\save\folder"`.

## Finding your save

```
%APPDATA%\eden\nand\user\save\<play-uid>\<account>\04007EF01F8AE000\000\
```

The editor finds this on its own (most recently played first) and remembers
the last folder you opened. Otherwise use **Open folder…** and pick any slot
file inside it.

## How it works

* **Every slot in the folder is loaded, and `Auto` opens first.** `Auto` is
  the live save the game continues from, so editing it alone is enough. The
  drop-down marks it ★ and labels the `Chapter_*` checkpoints.
* **Reload (F5) re-reads every slot from disk.** The editor also checks when
  you switch back to its window. If the game saved since, a slot with no
  unsaved edits is re-read on its own. If you have unsaved edits in it, Save
  warns you instead of overwriting the game's newer save.
* **Nothing touches the disk until you press Save** (Ctrl+S). Edits are held in
  memory; slots with pending changes get a ● in the drop-down and the Save button
  shows how many will be written.
  Quitting with unsaved changes asks first.
* **What the slots are.** `Auto` is your latest save on whichever lord's route
  you were last playing. `Route_<lord>` (e.g. `Route_Ism`) is that lord's route
  while you play someone else. `Chapter_<lord>_<part>_<chapter>` are chapter
  checkpoints, the points the game's "go back in time" feature returns to.
  `Global` holds settings only.
* **"Apply edits to this route's other saves"** (off by default) also writes
  each edit into the route's other live saves, e.g. that lord's `Route_*`.
  Another lord's route is never touched, and neither is any `Chapter_*`
  checkpoint, so each point in time keeps its own state. Open a checkpoint to
  edit it on its own.
* A unit is stored as **several copies** inside one slot. Every edit goes into
  all of them; the header shows "copies in sync", or offers *Make copies match*
  if they disagree.
* **Close the game before saving.**

![Convoy page](docs/convoy.png)

## Finding items

The item catalogue (Inventory and Convoy) searches English name, Japanese name
and id at once, as you type. Every search word must match, so `silver bow`
or `+3 sword` narrow things down. Use the **Type** filter (Sword, Lance, Tome,
Accessory, …) to cut it further. Forged copies show their level (`Silver Axe +2`)
even where the game's English text leaves it out.

When you pick an inventory slot, the catalogue only offers items of the same
kind (weapons for a weapon slot, etc.); tick *Allow any item type* to override.

**Icons:** items get a coloured dot by type and units an initials badge. Drop
PNGs into `icons/items/` and `icons/units/` to use real images — see
[icons/README.md](icons/README.md).

## Keyboard

| Key | Does |
|---|---|
| Ctrl+S | Save every changed slot |
| Ctrl+O | Open a save folder |
| Ctrl+F | Jump to the search box on the current page |
| F5 | Reload every slot from disk (asks first if you have unsaved edits) |
| Enter / double-click | Use the selected catalogue item |

## Fixes in 1.1.0

* Units come from the save's own unit pool (`fefw_core`), not from pattern
  matching, so the editor no longer invents "copies" of a unit, mislabels which
  copy is live, or writes a stat to every look-alike block.
* Item slots, skill lists, the convoy and gold are read the same way - gold at
  its fixed address (`GameUserData + 6`) in every slot, so the "locate it once by
  the amount shown" search and `money_sig.json` are gone.
* Convoy edits rebuild the list with every pointer rewritten, so adding an item
  can't knock the rest out of line.
* Undo / redo (Ctrl+Z, Ctrl+Y) over every edit, and **Snapshot** / **Restore...**
  copies of the whole slot folder.
* **Copy unit in...** (from another slot) and **Remove unit** (refused when
  something else in the save still points at the record).

## Known limits

* Only the class **id** and the class list are written. Usable weapons and class
  skills that come with a class are not recalculated here.
* A unit only has entries for the weapon ranks it owns, but a mastery can now be
  added: the record grows and every pointer after it is rewritten.
* EXP is a 16-bit running total (`(level - 1) * 100 + exp into the level`); the
  editor shows and writes the part inside the level, 0–99.
* Gold is read at `GameUserData + 6`. That matches the amount the game shows in
  `Auto` and the Theodora-route files; in the Ishmael files it reads 0, which
  hasn't been checked against the game yet.
* The convoy is a fixed row of 1329 slots, and it stays that way: adding an item
  fills the first empty slot and removing one empties its slot, the way the
  game itself deposits and withdraws. The list is rebuilt with its pointers
  rewritten, so nothing after it shifts out of line.
* A convoy damaged by an older version's "Add" (one written over empty slots)
  can't be read, so the Convoy page shows no list for that slot.
* Renown is an exp total (`GameUserData +14`). The level it lands on comes from
  the game's own `Reward.bin` table, so the editor shows exp, not a level.
* A flag whose name isn't in the game's data files shows as `unknown 0x…`. It is
  a real flag — just one nothing in the data names (about 43% of a mid-game
  save's 1.7k flags resolve).
* Enemy and NPC records can be viewed but not edited — their layout is only
  partly known.

## Files

```
editor.py            the GUI
editor_advanced.py   Player / Classes / Flags pages, support-conversation writes
fefw_core.py         the save object tree: records, resizing edits, convoy / mounts / flags
fefw_save.py         save container, unit records, all the edits (also a small CLI)
supports.py          support pair chart + conversation-flag lookup
unit_ids.json        person id  -> name
item_ids.json        item id    -> Japanese + English name
job_ids.json         class id   -> Japanese + English name
supports.json        support pair -> highest rank + per-rank conversation flag hashes
flag_names.json      flag hash  -> readable name (supports, recruits, achievements…)
build_flag_names.py  rebuilds flag_names.json: python build_flag_names.py <your romfs/GameData folder>
icons/               optional item / unit images
requirements.txt     zstandard
FEFW Save Editor.bat launcher (source install)
.github/workflows/   release build
```

`editor_settings.json` (theme, last folder, options) and `money_sig.json` (where
gold lives) are created next to the editor (or next to the `.exe`) on first use.

The three id files are generated from the game's own data files. A different
game version may need them rebuilt; unknown ids then show as
`unknown <hash>` instead of a name.

## Making a release

1. Bump `__version__` in `editor.py` (e.g. `"1.0.1"`) and commit.
2. Push a matching tag:

   ```
   git tag v1.0.1
   git push origin v1.0.1
   ```

GitHub Actions ([.github/workflows/release.yml](.github/workflows/release.yml))
builds the Windows `.exe` with PyInstaller, zips it with the README and the
`icons/` folder, adds a source zip and publishes the release. It can also be run
by hand from the Actions tab.

## Disclaimer

No warranty. Editing saves can corrupt them, and this was built by inspecting a
handful of save files — behaviour may differ on other game versions. Keep your
own backups.
