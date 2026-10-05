"""
Resolucao de caminhos do usuario para a acao `open_path`.

Pastas conhecidas (Downloads, Documentos...) sao lidas do Windows
(SHGetKnownFolderPath), porque podem estar redirecionadas para o OneDrive
e `~/Documents` nem existir.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Optional

_KNOWN_GUIDS = {
    "Downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
    "Documents": "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}",
    "Desktop": "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}",
    "Pictures": "{33E28130-4E1E-4676-835A-98395C3BC3BB}",
    "Videos": "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}",
    "Music": "{4BD8D571-6D19-48D3-BE97-422220080E43}",
}
_ALIASES = {
    "downloads": "Downloads", "download": "Downloads",
    "documentos": "Documents", "documents": "Documents", "meus documentos": "Documents",
    "area de trabalho": "Desktop", "desktop": "Desktop",
    "imagens": "Pictures", "fotos": "Pictures", "pictures": "Pictures",
    "videos": "Videos", "musicas": "Music", "music": "Music",
    "pasta pessoal": "Home", "pasta do usuario": "Home",
}
# Abrir um desses com startfile EXECUTA o arquivo (ou instala/monta/roda codigo): open_path recusa.
EXECUTABLE_EXT = {".exe", ".bat", ".cmd", ".ps1", ".psm1", ".psd1", ".ps1xml", ".vbs", ".vbe", ".vb", ".js",
                  ".jse", ".wsf", ".wsh", ".ws", ".msi", ".msp", ".mst", ".scr", ".com", ".lnk", ".hta", ".reg",
                  ".pif", ".cpl", ".msc", ".jar", ".url", ".chm", ".inf", ".scf", ".gadget", ".application",
                  ".appref-ms", ".appx", ".appxbundle", ".msix", ".msixbundle", ".appinstaller",
                  ".settingcontent-ms", ".library-ms", ".search-ms", ".searchconnector-ms", ".diagcab",
                  ".iso", ".img", ".vhd", ".vhdx", ".sys", ".dll", ".ocx"}


def is_network_path(path: str) -> bool:
    """Caminho de rede (\\\\servidor\\pasta, //servidor/pasta). So de TOCAR nele o Windows tenta
    autenticar no servidor e envia o hash da senha (NTLM): open_path recusa antes de qualquer acesso."""
    p = (path or "").strip().replace("/", "\\")
    return p.startswith("\\\\") or p.lower().startswith("file:")

_WIN_PATH = re.compile(r"([A-Za-z]:[\\/][^\"'<>|?*\n]*|%[A-Za-z_]+%[\\/]?[^\"'<>|?*\n]*|~[\\/][^\"'<>|?*\n]*)")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def known_folder(key: str) -> str:
    """Caminho real de uma pasta conhecida ('Downloads', 'Documents'...)."""
    home = os.path.expanduser("~")
    if key == "Home":
        return home
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD),
                        ("d3", wintypes.WORD), ("d4", ctypes.c_ubyte * 8)]
        guid = GUID()
        ctypes.oledll.ole32.CLSIDFromString(_KNOWN_GUIDS[key], ctypes.byref(guid))
        out = ctypes.c_wchar_p()
        ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(out))
        path = out.value
        ctypes.windll.ole32.CoTaskMemFree(out)
        if path:
            return path
    except Exception:
        pass
    return os.path.join(home, key)


def extract_path(text: str) -> Optional[str]:
    """Caminho citado no pedido: explicito (C:\\..., %VAR%, ~/) ou pasta conhecida
    (com subpasta opcional: 'pasta projetos dentro de documentos')."""
    t = text or ""
    m = _WIN_PATH.search(t)
    if m:
        return m.group(1).strip().rstrip(".,;")
    n = _norm(t)
    for alias in sorted(_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", n):
            base = known_folder(_ALIASES[alias])
            sub = re.search(rf"pasta\s+([\w\-. ]{{2,40}}?)\s+(?:dentro\s+)?(?:de|da|do|em|na|no)\s+(?:minha\s+|meus\s+)?{re.escape(alias)}\b", n)
            if sub and sub.group(1).strip() not in _ALIASES:
                return os.path.join(base, sub.group(1).strip())
            return base
    return None


def resolve_path(raw: str) -> str:
    """Normaliza: tira aspas, expande %VAR% e ~, traduz pasta conhecida."""
    p = (raw or "").strip().strip("\"'")
    if not p:
        return ""
    if _norm(p) in _ALIASES:
        return known_folder(_ALIASES[_norm(p)])
    p = os.path.expanduser(os.path.expandvars(p))
    return os.path.normpath(p)


def is_open_folder_request(task: str) -> bool:
    """'abra a pasta downloads', 'abrir C:\\projetos', 'mostre meus documentos'."""
    n = _norm(task)
    if not re.search(r"\b(abr\w*|mostr\w*|acess\w*|v[aá] para|ir para|entr\w*)\b", n):
        return False
    if re.search(r"\b(organiz|apag|exclu|delet|remov|mov|copi|renome|compact|duplicad|procur|encontr|busc"
                 r"|cri|escrev|digit|salv|cole|envi|mand|list|cont)", n):
        return False
    if re.search(r"https?://|www\.|\b(site|google|gmail|youtube|navegador|pesquis|baix)", n):
        return False
    return bool(extract_path(task)) and bool(re.search(r"\b(pasta|diretorio|caminho|explorador|[a-z]:[\\/])", n)
                                              or any(re.search(rf"\b{a}\b", n) for a in _ALIASES))
