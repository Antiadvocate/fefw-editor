# Source test candidate setup

Use this guide for `FEFW-Tutorials-Test-1.zip` / `feature/verified-tutorials`
and `FEFW-Blessings-Test-1.zip` / `feature/blessings-exp`.
The Blessings candidate includes the tested Tutorials changes. If Tutorials
already launches, reuse that Python environment: no new dependencies are
needed. Extract the new archive into its own directory and launch its
`editor.py`, rather than the old Tutorials copy. The window still shows the
upstream version number; identify the candidate by its `BUILD.txt` or commit.

## Python version and the reported installation failure

Python 3.12 is the recommended test interpreter. Tutorials automated tests have
passed on Python 3.10 and 3.12 on Linux and Windows. See each milestone's report
for its own validation. Python 3.15 is not validated.

The reported installation used CPython 3.15 and downloaded
`zstandard-0.25.0.tar.gz`, then failed with `Python.h: No such file or directory`.
That is a missing development header during a dependency source build. The
earlier `Defaulting to user installation` message is informational. Installing
headers would address that immediate compiler error, but would not establish
compatibility with Python 3.15. Use the tested interpreter for this milestone.

A virtual environment uses the interpreter that creates it: running the same
Python 3.15 command with `-m venv` does not switch it to 3.12.

## Bazzite: Ubuntu 24.04 Distrobox

These commands install dependencies inside a dedicated container. They do not
replace Bazzite's system Python. Distrobox shares your home directory and can
run graphical applications, so the extracted editor and copied saves remain
accessible. This is dependency isolation, not a sandbox for untrusted code.

1. From a Bazzite terminal, create the container and enter it. The first entry
   may take a few minutes to finish setup. If you already created this named
   container with Ubuntu 24.04, just enter it.

   ```sh
   distrobox create --name fefw-test --image docker.io/library/ubuntu:24.04
   distrobox enter fefw-test
   ```

2. Inside that container, install Ubuntu's prebuilt packages. Skip the original
   `pip install` step for this route.

   ```sh
   sudo apt update
   sudo apt install -y python3 python3-tk python3-zstandard
   /usr/bin/python3 -s -c 'import sys, tkinter, zstandard; print(sys.version); print("Tk", tkinter.TkVersion, "zstandard", zstandard.__version__)'
   ```

   Expect Python 3.12, a Tk version and a zstandard version, without an import
   error. The `-s` switch avoids loading packages from the shared user site.

3. In the same container terminal, change to the extracted directory containing
   `editor.py` (replace the example path with yours), then start the editor.

   ```sh
   cd "/path/to/extracted-editor"
   /usr/bin/python3 -s editor.py
   ```

For subsequent launches, run `distrobox enter fefw-test`, change to the source
directory and run the same editor command. The container package setup is only
needed once. Close the game before editing a copied save.

## Existing Python 3.12 installation

Tkinter must be available to that interpreter. Open a terminal in the extracted
directory containing `editor.py` and `requirements.txt`.

Linux/macOS:

```sh
python3.12 -m venv .venv-fefw312
.venv-fefw312/bin/python -m pip install --only-binary=:all: -r requirements.txt
.venv-fefw312/bin/python -c 'import tkinter, zstandard; print("Dependencies OK")'
.venv-fefw312/bin/python editor.py
```

Windows PowerShell, with Python 3.12 installed and available to the Python launcher:

```powershell
py -3.12 -m venv .venv-fefw312
.\.venv-fefw312\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv-fefw312\Scripts\python.exe -c "import tkinter, zstandard; print('Dependencies OK')"
.\.venv-fefw312\Scripts\python.exe editor.py
```

The binary-only option refuses an unavailable wheel instead of silently
starting a compiler build. If it reports no matching distribution, record the
Python version, OS and architecture before choosing another setup route.

## Test record

Record setup as **SETUP-01: PASS / FAIL / BLOCKED**, along with the interpreter
and dependency versions printed above and any error output. The Distrobox
instructions use officially supported components but have not yet been run on
the tester's Bazzite machine. Once the GUI opens, continue with
[the Tutorials guide](testing.md) or, for the new candidate,
[the Blessings guide](testing-blessings.md).

References checked 2026-11-15:

- [Bazzite: Distrobox](https://docs.bazzite.gg/Installing_and_Managing_Software/Distrobox/)
- [Distrobox: supported images](https://distrobox.it/compatibility/)
- [Ubuntu: available Python versions](https://ubuntu.com/developers/docs/reference/availability/python/)
- [Ubuntu 24.04: python3-tk](https://packages.ubuntu.com/noble/python3-tk)
- [Ubuntu 24.04: python3-zstandard](https://packages.ubuntu.com/noble/python3-zstandard)
