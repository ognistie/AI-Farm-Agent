"""
AI Farm Agent — Ponto de entrada principal (Desktop).

A interface antiga (Flask + HTML) foi descontinuada. `python main.py`
agora abre uma janela nativa em PySide6 + QML. Toda a logica de agentes,
core, memoria e scripts permanece intacta — apenas a camada de
apresentacao foi substituida.
"""

import ctypes
import os
import subprocess
import sys
from pathlib import Path


def tie_to_this_process(process) -> object:
    """O filho morre junto com este processo, mesmo se este for encerrado a forca (ex.: botao
    parar do VS Code). Usa so ctypes: aqui ainda pode ser um Python sem as dependencias.
    Devolve o job, que precisa continuar aberto."""
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                    ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", wintypes.DWORD),
                    ("f", ctypes.c_size_t), ("g", wintypes.DWORD), ("h", wintypes.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("Basic", Basic), ("Io", ctypes.c_uint64 * 6), ("sizes", ctypes.c_size_t * 4)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    limits = Extended()
    limits.Basic.LimitFlags = 0x2000                 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not job or not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) \
            or not kernel.AssignProcessToJobObject(job, int(process._handle)):
        raise OSError(ctypes.get_last_error(), "job object")
    return job


# Double-click/`python main.py` may select the global interpreter, which lacks
# the locked voice dependencies. Reuse the prepared project environment.
# Not os.execv: on Windows it starts a new process and ends this one, so whoever launched
# this (terminal, VS Code) loses track of the real app and cannot stop it.
if __name__ == '__main__':
    project_venv = Path(__file__).resolve().parent.parent / '.venv'
    no_console = Path(sys.executable).stem.lower() == 'pythonw'
    project_python = project_venv / 'Scripts' / ('pythonw.exe' if no_console else 'python.exe')
    if project_python.is_file() and Path(sys.prefix).resolve() != project_venv.resolve():
        child = subprocess.Popen([str(project_python), str(Path(__file__).resolve()), *sys.argv[1:]])
        try:
            _job = tie_to_this_process(child)
        except OSError:
            _job = None                              # sem job o app funciona, so nao morre junto
        while True:
            try:
                raise SystemExit(child.wait())
            except KeyboardInterrupt:
                continue                             # o app tambem recebeu e esta encerrando

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / '.env')
load_dotenv(BASE_DIR / '.env')


def _without_console() -> bool:
    return sys.stdout is None or Path(sys.executable).stem.lower() == 'pythonw'


def _send_output_to_log() -> None:
    """Aberto pelo atalho nao ha console: o que sairia nele vai para logs/app.log."""
    logs = BASE_DIR / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    path = logs / 'app.log'
    try:
        if path.stat().st_size > 5 * 1024 * 1024:
            path.replace(logs / 'app.previous.log')
    except OSError:
        pass
    stream = open(path, 'a', encoding='utf-8', buffering=1, errors='replace')
    sys.stdout = sys.stderr = stream


def _show_error(message: str) -> None:
    print(message)
    if _without_console():
        ctypes.windll.user32.MessageBoxW(None, message, "AI Farm Agent", 0x10)


def _require_env(var: str, hint: str) -> None:
    val = os.getenv(var, "")
    if not val or val.startswith("GERE_") or val == "sk-ant-COLE_SUA_CHAVE_AQUI":
        _show_error(f"{var} não configurada.\n{hint}")
        sys.exit(1)


# SECRET_KEY e AUTH_TOKEN eram exigidos pelo Flask. Mantidos como opcionais
# para compatibilidade com .env existentes — nao bloqueiam o desktop.

# Diretorios necessarios


def main() -> int:
    if _without_console():
        _send_output_to_log()
    _require_env('ANTHROPIC_API_KEY', 'Configure ANTHROPIC_API_KEY no .env do projeto.')
    for folder in ('captures', 'reports', 'desktop/data'):
        (BASE_DIR / folder).mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 60)
    print("  🌱 AI Farm Agent — Iniciando interface Desktop...")
    print("  Credencial do provedor configurada.")
    print("  🖥️  UI: PySide6 + QML")
    print("=" * 60 + "\n")

    try:
        from desktop.main import run
    except ImportError as e:
        _show_error(f"Não foi possível abrir a interface: {e}\nExecute scripts/setup.ps1.")
        return 2

    return run()


def _finish(code: int) -> None:
    """Sai de verdade. O encerramento normal do Python espera por bibliotecas nativas (audio,
    reconhecimento de fala) e pode travar com o agente ainda ouvindo e falando."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except (AttributeError, OSError, ValueError):
            pass
    os._exit(code)


if __name__ == "__main__":
    try:
        exit_code = main()
    except SystemExit as stop:
        exit_code = stop.code if isinstance(stop.code, int) else 1
    except Exception as error:
        import traceback
        traceback.print_exc()
        _show_error(f"O AI Farm Agent parou por um erro: {type(error).__name__}.\nDetalhes em logs/app.log.")
        exit_code = 1
    _finish(exit_code)
