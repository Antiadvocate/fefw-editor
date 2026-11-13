## Download

| File | For |
|---|---|
| **FEFW-Save-Editor-…-windows.zip** | Windows — no Python needed. Unzip anywhere and run `FEFW Save Editor.exe`. |
| **FEFW-Save-Editor-…-linux-x86_64.tar.gz** | Linux (glibc 2.35+: Arch, Fedora, Debian 12, Ubuntu 22.04 and newer) — no Python needed. Extract and run `./fefw-save-editor`. |
| FEFW-Save-Editor-…-source.zip | macOS / anyone with Python 3.10+: `pip install -r requirements.txt`, then `python editor.py`. |

**Close the game and back up your save folder first.** The first save next to
each slot also keeps the untouched original as `<slot>.bak`.

The `.exe` isn't code-signed, so Windows SmartScreen may say "Windows protected
your PC" — click *More info → Run anyway*. Some antivirus tools also flag
PyInstaller-built programs by mistake; the source zip is the same program if
you'd rather run it with Python.

Settings are saved next to the `.exe` (or Linux binary), so keep it in a folder you can write to
(not `Program Files`).
