"""
AI Farm Agent — Ponto de entrada principal (Desktop).

A interface antiga (Flask + HTML) foi descontinuada. `python main.py`
agora abre uma janela nativa em PySide6 + QML. Toda a logica de agentes,
core, memoria e scripts permanece intacta — apenas a camada de
apresentacao foi substituida.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _require_env(var: str, hint: str) -> None:
    val = os.getenv(var, "")
    if not val or val.startswith("GERE_") or val == "sk-ant-COLE_SUA_CHAVE_AQUI":
        print("\n" + "=" * 60)
        print(f"  ⚠️  {var} nao configurada!")
        print(f"  {hint}")
        print("=" * 60 + "\n")
        sys.exit(1)


_require_env(
    "ANTHROPIC_API_KEY",
    "Cole sua chave em .env. Obtenha em https://console.anthropic.com/",
)
# SECRET_KEY e AUTH_TOKEN eram exigidos pelo Flask. Mantidos como opcionais
# para compatibilidade com .env existentes — nao bloqueiam o desktop.

# Diretorios necessarios
BASE_DIR = Path(__file__).parent
(BASE_DIR / "captures").mkdir(exist_ok=True)
(BASE_DIR / "reports").mkdir(exist_ok=True)
(BASE_DIR / "desktop" / "data").mkdir(parents=True, exist_ok=True)


def main() -> int:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    print("\n" + "=" * 60)
    print("  🌱 AI Farm Agent — Iniciando interface Desktop...")
    print(f"  🔑 API Key: ...{api_key[-8:]}")
    print("  🖥️  UI: PySide6 + QML")
    print("=" * 60 + "\n")

    try:
        from desktop.main import run
    except ImportError as e:
        print("\n" + "=" * 60)
        print("  ❌ PySide6 nao instalado.")
        print("  Instale com:  pip install PySide6")
        print(f"  Erro original: {e}")
        print("=" * 60 + "\n")
        return 2

    return run()


if __name__ == "__main__":
    sys.exit(main())
