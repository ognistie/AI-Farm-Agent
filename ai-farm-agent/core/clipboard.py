"""
Colar texto sem perder o que o usuario tinha copiado.

Digitar via Ctrl+V e o jeito confiavel de escrever acentos e textos longos,
mas apagava a area de transferencia do usuario. Aqui guardamos o conteudo
anterior e devolvemos logo depois de colar.
"""

from __future__ import annotations

import time


def paste_text(text: str, restore: bool = True) -> None:
    import pyautogui
    try:
        import pyperclip
    except ImportError:
        pyautogui.write(text, interval=0.02)
        return
    previous = None
    if restore:
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = None
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    if previous is not None:
        time.sleep(0.25)          # o app le a area de transferencia antes de devolvermos
        try:
            pyperclip.copy(previous)
        except Exception:
            pass
