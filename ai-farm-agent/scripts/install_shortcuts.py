"""
Cria o atalho do AI Farm Agent na Area de Trabalho e no menu Iniciar, com icone proprio, sem
janela de console e com a mesma identidade da janela na barra de tarefas (assim o icone fixado
e o do app aberto ficam juntos). O Windows nao deixa programa nenhum fixar na barra sozinho.

    .venv/Scripts/python.exe ai-farm-agent/scripts/install_shortcuts.py
    .venv/Scripts/python.exe ai-farm-agent/scripts/install_shortcuts.py --remove
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

NAME = "AI Farm Agent"
ICON = APP / "desktop" / "assets" / "ai-farm-agent.ico"
ICON_SIZES = (16, 24, 32, 48, 64, 256)


def write_icon(path: Path = ICON) -> Path:
    """Gera o .ico a partir da marca do app (a mesma da janela). ICO aceita PNG por dentro."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QBuffer, QIODevice
    from PySide6.QtGui import QGuiApplication
    from desktop.main import brand_pixmap
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    images = []
    for size in ICON_SIZES:
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        brand_pixmap(size).save(buffer, "PNG")
        images.append((size, bytes(buffer.data())))
    del app
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, data = b"", b""
    for size, png in images:
        side = 0 if size >= 256 else size          # 0 = 256 no formato ICO
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + entries + data)
    return path


def shortcut_paths() -> list:
    from win32com.shell import shell, shellcon
    desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None, 0)
    programs = shell.SHGetFolderPath(0, shellcon.CSIDL_PROGRAMS, None, 0)
    return [Path(desktop) / f"{NAME}.lnk", Path(programs) / f"{NAME}.lnk"]


def launcher() -> Path:
    """O pythonw do ambiente do projeto: abre sem janela de console."""
    return APP.parent / ".venv" / "Scripts" / "pythonw.exe"


def write_shortcut(path: Path, app_id: str) -> None:
    import pythoncom
    from win32com.propsys import propsys, pscon
    from win32com.shell import shell
    link = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
    link.SetPath(str(launcher()))
    link.SetArguments(f'"{APP / "main.py"}"')
    link.SetWorkingDirectory(str(APP))
    link.SetIconLocation(str(ICON), 0)
    link.SetDescription("Assistente com agentes para o seu computador")
    store = link.QueryInterface(propsys.IID_IPropertyStore)
    store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(app_id, pythoncom.VT_LPWSTR))
    store.Commit()
    path.parent.mkdir(parents=True, exist_ok=True)
    link.QueryInterface(pythoncom.IID_IPersistFile).Save(str(path), True)


def read_shortcut(path: Path) -> dict:
    """Le o atalho gravado, para conferir o que ficou de fato no arquivo."""
    import pythoncom
    from win32com.propsys import propsys, pscon
    from win32com.shell import shell
    link = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
    link.QueryInterface(pythoncom.IID_IPersistFile).Load(str(path))
    store = link.QueryInterface(propsys.IID_IPropertyStore)
    return {"target": link.GetPath(0)[0], "arguments": link.GetArguments(), "icon": link.GetIconLocation()[0],
            "app_id": store.GetValue(pscon.PKEY_AppUserModel_ID).GetValue()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remove", action="store_true", help="apaga os atalhos criados por este script")
    args = parser.parse_args()
    paths = shortcut_paths()
    if args.remove:
        for path in paths:
            path.unlink(missing_ok=True)
            print("Removido:", path)
        return 0
    if not launcher().is_file():
        print("Ambiente ausente. Execute scripts/setup.ps1 primeiro.")
        return 1
    from desktop.main import APP_ID
    write_icon()
    for path in paths:
        write_shortcut(path, APP_ID)
        saved = read_shortcut(path)
        if saved["app_id"] != APP_ID or Path(saved["target"]).resolve() != launcher().resolve():
            print("Atalho gravado errado:", path)
            return 1
        print("Criado:", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
