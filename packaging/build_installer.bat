@echo off
rem Copyright (c) 2026 Shkour Bashtawi - https://github.com/ShkourBashtawi
rem Builds dist\GameTalk\GameTalk.exe (PyInstaller) and dist\GameTalk-Setup-<version>.exe (Inno Setup).
rem Set GAMETALK_CUDA=0 for a smaller build without NVIDIA GPU support.
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Run GameTalk.bat once first to create the environment.
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -q pyinstaller || goto fail
".venv\Scripts\python.exe" packaging\make_assets.py || goto fail
".venv\Scripts\pyinstaller" packaging\gametalk.spec --noconfirm --clean --distpath dist --workpath build\pyinstaller || goto fail

set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo.
    echo GameTalk.exe is ready in dist\GameTalk. Install Inno Setup 6 from jrsoftware.org
    echo to also build the setup file.
    exit /b 0
)
"%ISCC%" packaging\installer.iss || goto fail
echo.
echo Done: dist\GameTalk-Setup-*.exe
exit /b 0

:fail
echo Build failed.
exit /b 1
