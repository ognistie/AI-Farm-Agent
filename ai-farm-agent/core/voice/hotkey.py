"""
Atalho global do Windows (funciona com o app em segundo plano).

RegisterHotKey numa thread com fila de mensagens propria; o callback roda
nessa thread. Se outro programa ja usa a combinacao, `ok` fica False.
"""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

MODS = {"alt": 0x1, "ctrl": 0x2, "control": 0x2, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000
VKS = {"space": 0x20, "espaco": 0x20, "enter": 0x0D, "f8": 0x77, "f9": 0x78, "f10": 0x79}
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012


def parse(combo: str) -> tuple[int, int]:
    """'ctrl+alt+space' -> (mods, vk)."""
    mods, vk = 0, 0
    for part in (combo or "").lower().replace(" ", "").split("+"):
        if part in MODS:
            mods |= MODS[part]
        elif part in VKS:
            vk = VKS[part]
        elif len(part) == 1:
            vk = ord(part.upper())
    return mods, vk


class GlobalHotkey(threading.Thread):
    def __init__(self, combo: str, callback: Callable[[], None]):
        super().__init__(daemon=True, name="hotkey")
        self.combo, self.callback = combo, callback
        self.ok = False
        self._ready = threading.Event()
        self._tid = 0

    def start_and_wait(self, timeout: float = 2.0) -> bool:
        self.start()
        self._ready.wait(timeout)
        return self.ok

    def run(self) -> None:
        u = ctypes.windll.user32
        self._tid = ctypes.windll.kernel32.GetCurrentThreadId()
        mods, vk = parse(self.combo)
        self.ok = bool(vk) and bool(u.RegisterHotKey(None, 1, mods | MOD_NOREPEAT, vk))
        self._ready.set()
        if not self.ok:
            return
        msg = wintypes.MSG()
        try:
            while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    try:
                        self.callback()
                    except Exception as e:
                        print(f"  [voz] atalho falhou: {e}")
        finally:
            u.UnregisterHotKey(None, 1)

    def stop(self) -> None:
        if self._tid:
            ctypes.windll.user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
