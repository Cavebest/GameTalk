# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Encrypt API keys at rest with Windows DPAPI (bound to the current Windows user).

config.json only ever contains the encrypted blob; another user or another PC can't decrypt it.
"""

from __future__ import annotations

import base64
import ctypes
import logging
import sys
from ctypes import wintypes

log = logging.getLogger(__name__)

_PREFIX = "dpapi:"
_ENTROPY = b"GameTalk Translator"
_CRYPTPROTECT_UI_FORBIDDEN = 0x01


class _BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _blob(data: bytes) -> tuple[_BLOB, ctypes.Array]:
    buf = ctypes.create_string_buffer(data, len(data))
    return _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf


def _call(fn_name: str, data: bytes) -> bytes:
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    fn = getattr(crypt32, fn_name)
    fn.restype = wintypes.BOOL
    fn.argtypes = [
        ctypes.POINTER(_BLOB),
        ctypes.c_void_p,
        ctypes.POINTER(_BLOB),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_BLOB),
    ]
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    data_in, _keep1 = _blob(data)
    entropy, _keep2 = _blob(_ENTROPY)
    out = _BLOB()
    if not fn(
        ctypes.byref(data_in),
        None,
        ctypes.byref(entropy),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out),
    ):
        raise OSError(ctypes.get_last_error(), f"{fn_name} failed")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        kernel32.LocalFree(out.pbData)


def protect(secret: str) -> str:
    """Plain secret -> 'dpapi:<base64>' ('' stays '')."""
    if not secret:
        return ""
    if sys.platform != "win32":
        raise OSError("Key encryption is only available on Windows")
    blob = _call("CryptProtectData", secret.encode("utf-8"))
    return _PREFIX + base64.b64encode(blob).decode("ascii")


def unprotect(stored: str) -> str:
    """'dpapi:<base64>' -> plain secret; '' if empty or undecryptable (e.g. from another PC)."""
    if not stored or not stored.startswith(_PREFIX) or sys.platform != "win32":
        return ""
    try:
        return _call("CryptUnprotectData", base64.b64decode(stored[len(_PREFIX) :])).decode("utf-8")
    except (OSError, ValueError) as e:
        log.warning("Stored key could not be decrypted (%s); please re-enter it", type(e).__name__)
        return ""
