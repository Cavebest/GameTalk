# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Entry point: python -m gametalk  (or the `gametalk` GUI script)."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Privacy/noise: no Hugging Face telemetry; the hub is only contacted to fetch a missing model.
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

from gametalk import APP_NAME, __version__  # noqa: E402
from gametalk.config import ConfigStore, default_config_dir  # noqa: E402

log = logging.getLogger("gametalk")


def setup_logging(verbose: bool) -> None:
    log_dir = default_config_dir() / "logs"
    handlers: list[logging.Handler] = []
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                log_dir / "gametalk.log", maxBytes=512_000, backupCount=2, encoding="utf-8"
            )
        )
    except OSError:
        pass
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=handlers,
    )
    for noisy in ("httpx", "huggingface_hub", "faster_whisper"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gametalk", description=APP_NAME)
    parser.add_argument("--show", action="store_true", help="open the main window")
    parser.add_argument("--settings", action="store_true", help="open the settings page")
    parser.add_argument("--azure", action="store_true", help="open the cloud keys page")
    parser.add_argument("--test-mic", action="store_true", help="run a microphone test")
    parser.add_argument("--selftest", action="store_true", help="open the self-test")
    parser.add_argument("--phrasebook", action="store_true", help="open my phrasebook")
    parser.add_argument("--verbose", action="store_true", help="debug logging")
    parser.add_argument("--app", action="store_true", help=argparse.SUPPRESS)  # installed exe
    args, _unknown = parser.parse_known_args(argv)  # old shortcuts may pass retired flags
    if args.azure:
        command = "settings:azure"
    elif args.settings:
        command = "settings"
    elif args.test_mic:
        command = "test"
    elif args.selftest:
        command = "selftest"
    elif args.phrasebook:
        command = "phrasebook"
    elif args.show:
        command = "show"
    else:
        command = ""

    setup_logging(args.verbose)
    log.info("%s %s starting", APP_NAME, __version__)

    from PySide6.QtCore import QLockFile
    from PySide6.QtWidgets import QApplication, QMessageBox

    from gametalk import ipc
    from gametalk.app import Controller, TrayOverlay
    from gametalk.audio import Recorder
    from gametalk.gamepad import GamepadListener
    from gametalk.hotkey import HotkeyListener
    from gametalk.i18n import apply_layout_direction, set_language, tr
    from gametalk.speech import SpeechService
    from gametalk.teammates import TeammateListener
    from gametalk.tray import Tray
    from gametalk.voice import VoiceListener

    def excepthook(exc_type, exc, tb):
        # One failed slot must never take the whole app down.
        log.error("Unhandled error", exc_info=(exc_type, exc, tb))

    sys.excepthook = excepthook

    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)  # closing the window hides GameTalk to the tray
    try:
        from PySide6.QtQuickControls2 import QQuickStyle

        QQuickStyle.setStyle("Basic")  # the main window styles every control itself
    except ImportError:
        pass

    config_dir = default_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(config_dir / "gametalk.lock"))
    if not lock.tryLock(100):
        # Already running: hand the request to that instance instead of starting a second one.
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.AllowSetForegroundWindow(-1)  # let it bring its window up
        if ipc.send_command(command or "hello") is None:
            QMessageBox.information(None, APP_NAME, f"{APP_NAME} is already running (tray).")
        return 0

    store = ConfigStore()
    first_run = not store.path.exists()
    settings = store.load()
    set_language(settings.features.ui_language)
    apply_layout_direction(app)

    tray = Tray() if Tray.available() else None
    if tray is None:
        log.warning("System tray unavailable")
    try:
        from gametalk.overlay import Overlay

        overlay = Overlay()
        subtitles = Overlay()  # teammate subtitles get their own, independently placed overlay
    except Exception:
        log.exception("Overlay creation failed; falling back to tray notifications")
        overlay = TrayOverlay(tray)
        subtitles = TrayOverlay(tray)

    controller = Controller(
        store,
        settings,
        speech=SpeechService(),
        recorder=Recorder(),
        hotkey=HotkeyListener(),
        overlay=overlay,
        tray=tray,
        gamepad=GamepadListener(),
        teammates=TeammateListener(),
        subtitles=subtitles,
        voice=VoiceListener(),
    )
    controller.start()
    server = ipc.CommandServer(controller.handle_command)
    server.listen()
    if first_run:
        store.save(settings)
        command = command or "show"  # first start: show what GameTalk is
        if tray is not None:
            tray.notify(
                tr("Running in the tray. Hold {key}, speak, release.", key=settings.profile.hotkey)
            )
    if tray is None:
        # Without a tray the main window is the only UI, so closing it exits.
        app.setQuitOnLastWindowClosed(True)
        command = command if command.startswith(("settings", "show")) else "show"
    if command:
        controller.handle_command(command)

    rc = app.exec()
    server.close()
    clean = controller.shutdown()
    lock.unlock()
    log.info("Exited")
    logging.shutdown()  # flush logs before a possible hard exit
    if not clean:
        # A decode or Azure request is still running on the worker thread. Letting Qt destroy
        # that live QThread would abort the process, so leave immediately instead.
        os._exit(rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
