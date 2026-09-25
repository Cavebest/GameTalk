# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""One-click self-test: checks every part of GameTalk and says what to fix.

Quick facts are read on the UI thread; slow checks (opening the mic for 1 s, Azure, model
caches) run on a background thread so the window never freezes. The report contains no speech
content and no keys, so it's safe to copy and share.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from . import APP_NAME, __version__, theme
from .i18n import is_rtl, tr

ICONS = {"ok": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}


@dataclass
class Check:
    status: str  # ok | warn | fail | info
    title: str
    detail: str = ""
    fix: str = ""


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def _hf_cached(repo: str) -> bool:
    try:
        from huggingface_hub import snapshot_download

        snapshot_download(repo, local_files_only=True)
        return True
    except Exception:
        return False


def _bindings(hotkey) -> dict:
    b = getattr(hotkey, "bindings", {})
    return dict(b() if callable(b) else b)


def snapshot(c) -> dict:
    """Facts that must be read on the UI thread."""
    from .app import TrayOverlay

    p, f, tm = c.profile, c.features, c.settings.teammates
    return {
        "loaded": c.speech.loaded,
        "loading": c.speech.loading,
        "summary": c.speech.summary,
        "last_error": c.speech.last_error,
        "model": p.model,
        "uses_whisper": p.uses_whisper or (tm.enabled and tm.recognizer != "azure"),
        "device_pref": c.settings.compute_device,
        "microphone": p.microphone,
        "recording": c.recording,
        "voice_mode": p.hotkey_mode == "voice",
        "hotkey_running": getattr(c.hotkey, "running", True),
        "bindings": _bindings(c.hotkey),
        "overlay_ok": not isinstance(c.overlay, TrayOverlay),
        "tray": c.tray is not None,
        "azure_needed": p.uses_azure
        or (tm.enabled and "azure" in (tm.recognizer, tm.translator))
        or (f.quick_text_enabled and f.quick_text_translator == "azure"),
        "creds": c.azure_credentials(),
        "team_enabled": tm.enabled,
        "team_device": tm.device,
        "team_local": tm.enabled and tm.translator == "local",
        "text_local": f.quick_text_enabled and f.quick_text_translator in ("local", "auto"),
        "gamepad": f.gamepad_enabled,
        "exclusive_fullscreen": c._exclusive_fullscreen(),
    }


def run_checks(s: dict, open_mic=None) -> list[Check]:
    """Slow checks; safe to run on a background thread."""
    from .speech import cuda_device_count

    out: list[Check] = []

    # Speech engine
    if s["loading"]:
        out.append(Check("info", tr("Speech engine"), tr("Still loading…")))
    elif s["loaded"]:
        out.append(Check("ok", tr("Speech engine"), s["summary"]))
    else:
        out.append(
            Check(
                "fail",
                tr("Speech engine"),
                tr(s["last_error"] or "Speech model isn't loaded."),
                tr("Settings → Speech: pick another model, or connect to the internet once."),
            )
        )

    # GPU
    gpus = cuda_device_count() if sys.platform == "win32" else 0
    on_cpu = "CPU" in (s["summary"] or "")
    if gpus and s["uses_whisper"] and on_cpu and s["device_pref"] != "cpu":
        out.append(
            Check(
                "warn",
                tr("Graphics card"),
                tr("An NVIDIA GPU was found but Whisper runs on the CPU."),
                tr("Settings → Speech → Run on: Auto. Update the NVIDIA driver if it persists."),
            )
        )
    elif gpus:
        out.append(Check("ok", tr("Graphics card"), tr("NVIDIA GPU available")))
    else:
        out.append(
            Check(
                "info",
                tr("Graphics card"),
                tr("No NVIDIA GPU: Whisper uses the CPU (slower). Azure mode avoids this."),
            )
        )

    # Microphone
    if s["recording"]:
        out.append(Check("info", tr("Microphone"), tr("Skipped: you're recording right now.")))
    elif open_mic is not None:
        try:
            audio = open_mic(s["microphone"])
            peak = float(np.max(np.abs(audio))) if audio.size else 0.0
            if audio.size == 0 or peak == 0.0:
                out.append(
                    Check(
                        "fail",
                        tr("Microphone"),
                        tr("The microphone gives no sound at all."),
                        tr(
                            "Unmute it, pick your real microphone in Settings → Microphone, or "
                            "allow it in Windows Privacy → Microphone."
                        ),
                    )
                )
            elif peak < 0.002:
                out.append(
                    Check(
                        "warn",
                        tr("Microphone"),
                        tr("Works, but very quiet."),
                        tr("Raise the microphone volume in Windows Sound settings."),
                    )
                )
            else:
                out.append(Check("ok", tr("Microphone"), tr("Opens and picks up sound.")))
        except Exception as e:
            out.append(
                Check(
                    "fail",
                    tr("Microphone"),
                    tr(str(e)),
                    tr("Pick another microphone in Settings → Microphone."),
                )
            )

    # Hotkey / overlay / tray
    if s["hotkey_running"]:
        keys = ", ".join(f"{k}" for k in s["bindings"].values() if k) or "—"
        out.append(Check("ok", tr("Hotkeys"), tr("Listening for: {keys}", keys=keys)))
    else:
        out.append(
            Check(
                "fail",
                tr("Hotkeys"),
                tr("The hotkey listener isn't running."),
                tr("Restart GameTalk."),
            )
        )
    if s["overlay_ok"]:
        out.append(Check("ok", tr("Overlay"), tr("Ready (click-through, never takes focus).")))
    else:
        out.append(
            Check(
                "fail",
                tr("Overlay"),
                tr("The overlay window couldn't be created; results go to tray notifications."),
                tr("Update your graphics driver and restart GameTalk."),
            )
        )
    if s["exclusive_fullscreen"]:
        out.append(
            Check(
                "warn",
                tr("Fullscreen"),
                tr("A game is in exclusive fullscreen now — the overlay can't appear over it."),
                tr("Switch the game to Borderless or Windowed."),
            )
        )
    if _is_admin():
        out.append(Check("info", tr("Administrator"), tr("GameTalk runs as administrator.")))
    else:
        out.append(
            Check(
                "info",
                tr("Administrator"),
                tr(
                    "GameTalk runs as a normal user. Games started as administrator won't "
                    "send it the hotkey — then run GameTalk as administrator too."
                ),
            )
        )

    # Azure
    if s["azure_needed"]:
        from .azure import check_connection

        for ok, msg in check_connection(s["creds"]):
            head, sep, rest = msg.partition(" (")
            out.append(
                Check(
                    "ok" if ok else "fail",
                    "Azure",
                    tr(head) + sep + rest,
                    "" if ok else tr("Settings → Azure: check the key and region."),
                )
            )
    else:
        out.append(Check("info", "Azure", tr("Not used by your current settings.")))

    # Offline models
    from .local_mt import AR_EN, EN_AR

    if s["uses_whisper"] and s["model"] and not os.path.isdir(s["model"]):
        repo = f"Systran/faster-whisper-{s['model']}"
        cached = _hf_cached(repo)
        out.append(
            Check(
                "ok" if cached else "warn",
                tr("Whisper model"),
                s["model"] + (" ✓" if cached else ""),
                "" if cached else tr("It will download on first use (internet needed once)."),
            )
        )
    for needed, repo, label in (
        (s["team_local"], EN_AR, tr("Offline translator (English → Arabic)")),
        (s["text_local"], AR_EN, tr("Offline translator (Arabic → English)")),
    ):
        if needed:
            cached = _hf_cached(repo)
            out.append(
                Check(
                    "ok" if cached else "warn",
                    label,
                    tr("Downloaded") if cached else tr("Not downloaded yet (~160 MB)."),
                    "" if cached else tr("It will download on first use (internet needed once)."),
                )
            )

    # Teammates / gamepad
    if s["team_enabled"]:
        from .teammates import output_devices

        devices = output_devices()
        if s["team_device"] and s["team_device"] not in devices:
            out.append(
                Check(
                    "fail",
                    tr("Teammate subtitles"),
                    tr("The selected output device isn't connected."),
                    tr("Settings → Teammate subtitles → Listen to."),
                )
            )
        else:
            out.append(Check("ok", tr("Teammate subtitles"), tr("Output device available.")))
    if s["gamepad"]:
        from .gamepad import XINPUT_STATE, _load_xinput

        get = _load_xinput()
        found = False
        if get is not None:
            st = XINPUT_STATE()
            found = any(get(i, ctypes.byref(st)) == 0 for i in range(4))
        out.append(
            Check(
                "ok" if found else "warn",
                tr("Game controller"),
                tr("Controller connected.") if found else tr("No controller connected."),
                ""
                if found
                else tr("Connect an Xbox controller (or use Steam Input / DS4Windows)."),
            )
        )

    # Disk space for models
    cache = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    try:
        free_gb = shutil.disk_usage(cache.anchor or str(Path.home())).free / 1e9
        if free_gb < 2:
            out.append(
                Check(
                    "warn",
                    tr("Disk space"),
                    tr("{gb:.1f} GB free", gb=free_gb),
                    tr("Models need up to 3 GB. Free some space."),
                )
            )
        else:
            out.append(Check("ok", tr("Disk space"), tr("{gb:.1f} GB free", gb=free_gb)))
    except OSError:
        pass
    return out


def report_text(checks: list[Check]) -> str:
    lines = [f"{APP_NAME} {__version__} — self-test"]
    for ch in checks:
        lines.append(
            f"{ICONS[ch.status]} {ch.title}: {ch.detail}" + (f" → {ch.fix}" if ch.fix else "")
        )
    return "\n".join(lines)


class _Relay(QObject):
    done = Signal(object)


class DiagnosticsDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.c = controller
        self.checks: list[Check] = []
        self.setWindowTitle(tr("{app} — Self-test", app=tr(APP_NAME)))
        if is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        theme.apply(
            self,
            "QTextBrowser { background: #161a22; border: 1px solid #232937; border-radius: 8px;"
            " padding: 8px; font-size: 10.5pt; }",
        )
        self.resize(640, 560)
        lay = QVBoxLayout(self)
        self.summary = QLabel(tr("Checking…"))
        self.summary.setStyleSheet("font-size: 13pt; font-weight: 600")
        lay.addWidget(self.summary)
        self.view = QTextBrowser()
        lay.addWidget(self.view, 1)
        row = QHBoxLayout()
        self.again = QPushButton(tr("Run again"))
        self.again.clicked.connect(self.run)
        copy = QPushButton(tr("Copy report"))
        copy.setToolTip(tr("Contains no speech and no keys — safe to share."))
        copy.clicked.connect(lambda: QApplication.clipboard().setText(report_text(self.checks)))
        close = QPushButton(tr("Close"))
        close.clicked.connect(self.close)
        row.addWidget(self.again)
        row.addWidget(copy)
        row.addStretch(1)
        row.addWidget(close)
        lay.addLayout(row)
        self._relay = _Relay(self)
        self._relay.done.connect(self._show)
        self.run()

    def run(self) -> None:
        self.again.setEnabled(False)
        self.summary.setText(tr("Checking…"))
        self.view.setHtml("")
        facts = snapshot(self.c)
        relay = self._relay
        open_mic = self._open_mic

        def work():
            try:
                checks = run_checks(facts, open_mic)
            except Exception as e:  # never leave the dialog hanging
                checks = [Check("fail", tr("Self-test"), f"{type(e).__name__}")]
            relay.done.emit(checks)

        threading.Thread(target=work, name="gametalk-selftest", daemon=True).start()

    @staticmethod
    def _open_mic(device: str) -> np.ndarray:
        import time

        from .audio import Recorder

        rec = Recorder()
        rec.start(device)
        time.sleep(1.0)
        return rec.stop()

    def _show(self, checks: list[Check]) -> None:
        self.checks = checks
        self.again.setEnabled(True)
        fails = sum(c.status == "fail" for c in checks)
        warns = sum(c.status == "warn" for c in checks)
        if fails:
            self.summary.setText(tr("❌ {n} problem(s) found", n=fails))
        elif warns:
            self.summary.setText(tr("⚠️ Works, with {n} warning(s)", n=warns))
        else:
            self.summary.setText(tr("✅ Everything looks good"))
        direction = "rtl" if is_rtl() else "ltr"
        rows = []
        for ch in checks:
            fix = f'<br><span style="color:#38bdf8">→ {ch.fix}</span>' if ch.fix else ""
            rows.append(
                f"<p>{ICONS[ch.status]} <b>{ch.title}</b><br>"
                f'<span style="color:#aab2c0">{ch.detail}</span>{fix}</p>'
            )
        self.view.setHtml(f'<div dir="{direction}">' + "".join(rows) + "</div>")
