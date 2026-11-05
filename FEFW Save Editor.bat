@echo off
rem Launch the Fortune's Weave save editor. Needs Python 3.10+ with zstandard.
setlocal
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0editor.py"
) else (
    start "" python "%~dp0editor.py"
)
