import sys
import time

import pytest

from gametalk.credentials import protect, unprotect

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="DPAPI is Windows-only")


@windows_only
def test_dpapi_round_trip_and_ciphertext_hides_key():
    stored = protect("my-azure-key-123")
    assert stored.startswith("dpapi:")
    assert "my-azure-key-123" not in stored
    assert unprotect(stored) == "my-azure-key-123"


def test_empty_and_garbage():
    assert protect("") == ""
    assert unprotect("") == ""
    assert unprotect("plaintext-key") == ""  # never accept unencrypted values
    assert unprotect("dpapi:bm90IHJlYWw=") == ""  # undecryptable blob -> re-enter key


CLIENT = """
import sys
from PySide6.QtCore import QCoreApplication
app = QCoreApplication([])
from gametalk import ipc
ipc.server_name = lambda: "GameTalkTranslator-pytest"
print(ipc.send_command(sys.argv[1], 3000))
"""


def test_ipc_round_trip_across_processes(qapp, monkeypatch):
    """Same shape as real use: the launcher process talks to the running app process."""
    import subprocess

    from PySide6.QtCore import QCoreApplication

    from gametalk import ipc

    monkeypatch.setattr(ipc, "server_name", lambda: "GameTalkTranslator-pytest")
    received = []

    def handler(cmd):
        received.append(cmd)
        return "pong:" + cmd

    server = ipc.CommandServer(handler)
    assert server.listen()
    proc = subprocess.Popen(
        [sys.executable, "-c", CLIENT, "status"], stdout=subprocess.PIPE, text=True
    )
    while proc.poll() is None:
        QCoreApplication.processEvents()
        time.sleep(0.01)
    server.close()
    assert received == ["status"]
    assert proc.stdout.read().strip() == "pong:status"
    assert ipc.send_command("status", 200) is None  # nothing listening any more
