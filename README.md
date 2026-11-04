# Fortune's Weave Save Editor

A small save editor for **Fire Emblem: Fortune's Weave** saves created by the
Eden / eglantine Switch emulator. Plain Python + Tkinter, no install beyond one
library.

> **Unofficial and reverse-engineered.** Back up your save folder before using it.

## Features

| Tab | What you can edit |
|---|---|
| **Unit** | Level, EXP, Max HP, and all nine stats (HP, Str, Mag, Dex, Spd, Lck, Def, Res, Cha) |
| **Unit** | Class — pick any class the game knows, English name + original id |
| **Aptitude** | Skill experience for every skill family, with the grade (E → S+) shown next to it |
| **Items** | The items a unit is carrying (swap the id, keep the uses) |
| **Convoy** | Shared storage — append, replace or clear rows |
| **Money** | Gold — search for the amount the game shows, then set it |

Skill families the editor understands: Swords, Lances, Axes, Bows, Fists,
Black Magic, White Magic, Infantry, Riding, Heavy Armor, Flying, Authority.

Grade thresholds used when you pick a letter: `E 0, E+ 40, D 100, D+ 180,
C 300, C+ 460, B 680, B+ 960, A 1320, A+ 1760, S 2520, S+ 3600`.

## Requirements

* Python 3.10 or newer
* `pip install -r requirements.txt` (only `zstandard`)

## Running it

```
pip install -r requirements.txt
python editor.py
```

or double-click **FEFW Save Editor.bat** on Windows.

## Finding your save

```
%APPDATA%\eden\nand\user\save\<play-uid>\<account>\04007EF01F8AE000\000\
```

The editor finds this automatically and lists every slot file
(`Auto`, `Chapter_*`, `Route_*`) with its unit count and timestamp.

## How it behaves

* **One slot file at a time.** Whatever file is selected in the dropdown is what
  you are editing, and *Save file* writes only that file.
* **Mid-chapter the game resumes from a `Chapter_*` slot, not `Auto`.** If your
  edit "doesn't show up", this is usually why — the Aptitude tab has a button
  that copies the grades into every slot in the folder.
* A unit is stored as **several copies** inside one save file. The editor shows
  one row per unit, writes every copy, and tells you when the copies disagree.
* **Close the game before writing.** The first write next to a slot leaves a
  `.bak` file.

## Known limits

* Only the class **id** is written. The game derives movement, usable weapons,
  class skills and max HP from the class; those are not recalculated here.
* A unit only has entries for the skills it owns. The others display `E` in game
  and can't be added from here — the list is fixed-size inside the record.
* Gold needs the amount the game is currently showing.
* Renown and the material/gift bag are not editable.

## Files

```
editor.py            the GUI
fefw_save.py         save container, unit records, all the edits
unit_ids.json        person id  -> name
item_ids.json        item id    -> Japanese + English name
job_ids.json         class id   -> Japanese + English name
requirements.txt     zstandard
FEFW Save Editor.bat launcher
```

The three JSON files are generated from the game's own data files. A different
game version may need them rebuilt; unknown ids then show as
`unknown <hash>` instead of a name.

## Disclaimer

No warranty. Editing saves can corrupt them, and this was built by inspecting a
single save file — behaviour may differ on other game versions. Keep your own
backups.
