# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Tiny local command channel so a second launch (or a script) can drive the running app.

Uses a per-user Windows named pipe via QLocalServer. Nothing listens on the network.
Commands: show, status, stats, settings[:page], test, reload, preview, selftest, phrasebook,
hello, quit.
"""

from __future__ import annotations

import getpass
import logging
from collections.abc import Callable

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket

log = logging.getLogger(__name__)


def server_name() -> str:
    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    return f"GameTalkTranslator-{user}"


def send_command(command: str, timeout_ms: int = 1500) -> str | None:
    """Send one command to the running app. Returns its reply, or None if it isn't running."""
    sock = QLocalSocket()
    sock.connectToServer(server_name())
    if not sock.waitForConnected(timeout_ms):
        return None
    try:
        sock.write((command + "\n").encode("utf-8"))
        if not sock.waitForBytesWritten(timeout_ms):
            return None
        data = b""
        while not data.endswith(b"\n"):
            if not sock.waitForReadyRead(timeout_ms):
                break
            data += bytes(sock.readAll().data())
        return data.decode("utf-8", "replace").strip()
    finally:
        sock.disconnectFromServer()


def is_running() -> bool:
    return send_command("status", 500) is not None


class CommandServer(QObject):
    def __init__(self, handler: Callable[[str], str], parent=None):
        super().__init__(parent)
        self._handler = handler
        self._server = QLocalServer(self)
        self._server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self._server.newConnection.connect(self._on_connection)

    def listen(self) -> bool:
        QLocalServer.removeServer(server_name())  # clear a stale pipe from a crashed run
        ok = self._server.listen(server_name())
        if not ok:
            log.warning("Command channel unavailable: %s", self._server.errorString())
        return ok

    def close(self) -> None:
        self._server.close()

    def _on_connection(self) -> None:
        while self._server.hasPendingConnections():
            sock = self._server.nextPendingConnection()
            buf = bytearray()

            def on_ready(sock=sock, buf=buf):
                buf.extend(bytes(sock.readAll().data()))
                if b"\n" not in buf:
                    return
                command = buf.split(b"\n", 1)[0].decode("utf-8", "replace").strip()
                try:
                    reply = self._handler(command)
                except Exception:
                    log.exception("Command %r failed", command)
                    reply = "error"
                sock.write((reply + "\n").encode("utf-8"))
                sock.flush()
                sock.disconnectFromServer()

            sock.readyRead.connect(on_ready)
            sock.disconnected.connect(sock.deleteLater)
            if sock.bytesAvailable():
                on_ready()
