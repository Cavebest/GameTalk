@echo off
rem Copyright (c) 2026 Shkour Bashtawi - https://github.com/ShkourBashtawi
rem GameTalk Translator - double-click to open the launcher.
rem First run: creates .venv and installs everything (a few minutes, needs internet once).
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" goto launch

echo ============================================================
echo  GameTalk Translator - first-time setup
echo ============================================================
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo Python 3.10+ was not found. Install it from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH", then run this file again.
    pause
    exit /b 1
)

echo Creating virtual environment...
%PY% -m venv .venv || goto fail
".venv\Scripts\python.exe" -m pip install --upgrade pip || goto fail

set "EXTRAS="
where nvidia-smi >nul 2>nul && set "EXTRAS=[cuda]"
if defined EXTRAS (echo NVIDIA GPU found - installing with GPU support.) else (echo No NVIDIA GPU found - installing CPU version.)
".venv\Scripts\python.exe" -m pip install -e ".%EXTRAS%" || goto fail
echo Setup complete.

:launch
start "" ".venv\Scripts\pythonw.exe" -m gametalk.launcher %*
exit /b 0

:fail
echo.
echo Setup failed - see the messages above. Delete the .venv folder and try again.
pause
exit /b 1
