import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")  # the main window renders off-screen


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWidgets import QApplication

    QQuickStyle.setStyle("Basic")  # like the app: before any QML is loaded
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _close_main_windows():
    """A test that opened the main window (even via a queued command) closes it again."""
    yield
    from PySide6.QtWidgets import QApplication

    if QApplication.instance() is None:
        return
    from gametalk.hub import HubWindow

    QApplication.processEvents()
    for w in list(HubWindow.instances):
        w.close()
    QApplication.processEvents()  # runs the deferred teardown
