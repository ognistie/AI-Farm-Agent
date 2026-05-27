"""
cleanup_old_files.py — Rotaciona artefatos antigos.

Mantem apenas N arquivos mais recentes em cada pasta volumosa:
  - captures/         50 screenshots (resto deletado)
  - reports/*.html    10 relatorios HTML
  - reports/*.json    50 relatorios JSON (sao pequenos)
  - logs/             10 arquivos de log
  - memory/workflows/.corrupted/   limpa tudo (legado de bug antigo)

Pode ser chamado:
  - manualmente: `python scripts/cleanup_old_files.py`
  - automatico:  `from scripts.cleanup_old_files import run_cleanup` no startup

Use --dry-run para ver o que seria removido sem deletar.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


BASE = Path(__file__).resolve().parent.parent

# pasta -> (padrao, manter_n)
ROTATION_POLICY = [
    ("captures",                "*.png",   50),
    ("captures",                "*.jpg",   50),
    ("reports",                 "*.html",  10),
    ("reports",                 "*.json",  50),
    ("logs",                    "*",       10),
]

# pastas que devem ser ESVAZIADAS (legado de bugs antigos)
PURGE_DIRS = [
    "memory/workflows/.corrupted",
]


def _rotate(folder: Path, pattern: str, keep: int, dry: bool = False) -> tuple[int, int]:
    """Mantem `keep` arquivos mais recentes do padrao. Retorna (removidos, bytes_liberados)."""
    if not folder.exists():
        return 0, 0
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    to_remove = files[keep:]
    bytes_freed = 0
    for f in to_remove:
        try:
            bytes_freed += f.stat().st_size
            if not dry:
                f.unlink()
        except OSError:
            continue
    return len(to_remove), bytes_freed


def _purge(folder: Path, dry: bool = False) -> tuple[int, int]:
    """Apaga TODOS os arquivos em folder. Retorna (removidos, bytes)."""
    if not folder.exists():
        return 0, 0
    removed = 0
    bytes_freed = 0
    for f in folder.iterdir():
        if f.is_file():
            try:
                bytes_freed += f.stat().st_size
                if not dry:
                    f.unlink()
                removed += 1
            except OSError:
                continue
    return removed, bytes_freed


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def run_cleanup(verbose: bool = True, dry: bool = False) -> dict:
    """Executa a rotacao. Retorna dict com totais."""
    total_files = 0
    total_bytes = 0
    by_folder: dict[str, dict] = {}

    for folder, pattern, keep in ROTATION_POLICY:
        path = BASE / folder
        n, b = _rotate(path, pattern, keep, dry=dry)
        if n:
            key = f"{folder}/{pattern}"
            by_folder[key] = {"removed": n, "bytes": b}
            total_files += n
            total_bytes += b
            if verbose:
                print(f"  {'[DRY] ' if dry else ''}{folder}/{pattern}: -{n} arquivos ({_human(b)})")

    for folder in PURGE_DIRS:
        path = BASE / folder
        n, b = _purge(path, dry=dry)
        if n:
            by_folder[folder] = {"removed": n, "bytes": b, "mode": "purge"}
            total_files += n
            total_bytes += b
            if verbose:
                print(f"  {'[DRY] ' if dry else ''}{folder}: PURGE -{n} arquivos ({_human(b)})")

    if verbose:
        print(f"\nTotal: -{total_files} arquivos · {_human(total_bytes)} liberados")

    return {"removed": total_files, "bytes_freed": total_bytes, "by_folder": by_folder}


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv or "-n" in sys.argv
    if dry:
        print("[DRY RUN — nada sera deletado]\n")
    run_cleanup(verbose=True, dry=dry)
