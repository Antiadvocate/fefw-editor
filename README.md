# Fortune's Weave Save Editor

A save editor for **Fire Emblem: Fortune's Weave** saves created by the
Eden / eglantine Switch emulator. Plain Python + Tkinter, one extra library.

> **Unofficial and reverse-engineered.** The first save next to each slot keeps
> the untouched original as `<slot>.bak` — but keep your own backup too.

![Units page](docs/units.png)

## What you can edit

| Page | Tab | What |
|---|---|---|
| **Units** | Stats | Level, EXP and all nine stats (HP, Str, Mag, Dex, Spd, Lck, Def, Res, Cha) |
| | Weapon ranks | Rank EXP for every rank the unit owns, with the letter grade, progress to the next grade and a one-click "set every rank to…" |
| | Inventory | Swap any carried item for another, picked from a searchable catalogue |
| | Class | Pick any class the game knows (searchable, English + internal name) |
| **Convoy** | | Add items, replace a row, change quantities, clear rows |
| **Gold** | | Set gold — locate it once by the amount the game shows, then it's found automatically |

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

* **Every slot in the folder is loaded.** The slot drop-down lists `Auto`,
  `Chapter_*` and `Route_*` with unit count and time; the newest one is marked
  ★ and opened first.
* **Nothing touches the disk until you press Save** (Ctrl+S). Edits are held in
  memory; slots with pending changes get a ● in the drop-down and the Save button
  shows how many will be written. *Discard changes* (F5) re-reads everything.
  Quitting with unsaved changes asks first.
* **"Apply edits to every slot in this folder"** (on by default) writes each
  edit into the same unit / convoy / gold in every slot. Mid-chapter the game
  resumes from a `Chapter_*` slot rather than `Auto`, so an edit made to one slot
  alone can look like it did nothing. Turn it off to edit one slot only.
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
| F5 | Discard changes and re-read from disk |
| Enter / double-click | Use the selected catalogue item |
| Delete | Clear the selected convoy row(s) |

## Known limits

* Only the class **id** is written. The game derives movement, usable weapons,
  class skills and max HP from the class; those are not recalculated here.
* A unit only has entries for the weapon ranks it owns. The others display `E` in
  game and can't be added from here — the list is fixed-size inside the record.
* Max HP is not stored in the save — only current HP can be edited.
* Gold needs to be located once using the amount the game is currently showing
  (not 0).
* An item already in the convoy can't be added as a second stack — change its
  quantity instead.
* Renown and the material/gift bag are not editable.

## Files

```
editor.py            the GUI
fefw_save.py         save container, unit records, all the edits (also a small CLI)
unit_ids.json        person id  -> name
item_ids.json        item id    -> Japanese + English name
job_ids.json         class id   -> Japanese + English name
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
