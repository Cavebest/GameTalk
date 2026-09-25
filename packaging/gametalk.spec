# -*- mode: python ; coding: utf-8 -*-
# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
# PyInstaller build: one folder, windowed GameTalk.exe. Run through packaging\build_installer.bat.
import glob
import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_data_files

HERE = os.path.dirname(os.path.abspath(SPEC))  # noqa: F821 (provided by PyInstaller)
SITE = next(p for p in sys.path if p.endswith("site-packages"))
WITH_CUDA = os.environ.get("GAMETALK_CUDA", "1") == "1"

datas, binaries, hiddenimports = [], [], []
for pkg in ("faster_whisper", "ctranslate2", "azure.cognitiveservices.speech", "soundcard", "cmudict"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h
datas += collect_data_files("_sounddevice_data")
hiddenimports += ["sentencepiece", "gametalk.launcher", "gametalk.__main__"]

if WITH_CUDA:  # cuBLAS so Whisper can use an NVIDIA GPU (found at runtime under nvidia/*/bin)
    for dll in glob.glob(os.path.join(SITE, "nvidia", "cublas", "bin", "*.dll")):
        if "nvblas" not in os.path.basename(dll):
            binaries.append((dll, os.path.join("nvidia", "cublas", "bin")))

a = Analysis(  # noqa: F821
    [os.path.join(HERE, "entry.py")],
    pathex=[os.path.dirname(HERE)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "pytest", "IPython", "torch", "tensorflow"],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GameTalk",
    console=False,
    icon=os.path.join(HERE, "gametalk.ico"),
    version=os.path.join(HERE, "version_info.txt"),
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="GameTalk", upx=False)  # noqa: F821
