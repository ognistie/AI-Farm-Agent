"""
AI Farm Agent — Ponto de entrada principal.
Carrega .env, cria diretórios, inicia servidor Flask e abre o browser.
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Verifica API key
api_key = os.getenv("ANTHROPIC_API_KEY", "")
if not api_key or api_key == "sk-ant-COLE_SUA_CHAVE_AQUI":
    print("\n" + "=" * 60)
    print("  ⚠️  ANTHROPIC_API_KEY não configurada!")
    print("  Edite o arquivo .env e cole sua chave da API.")
    print("  Obtenha em: https://console.anthropic.com/")
    print("=" * 60 + "\n")
    sys.exit(1)

# Cria diretórios necessários
BASE_DIR = Path(__file__).parent
CAPTURES_DIR = BASE_DIR / "captures"
REPORTS_DIR = BASE_DIR / "reports"
CAPTURES_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Configurações do servidor
HOST = "127.0.0.1"
PORT = 5000


def open_browser():
    """Abre o browser após um pequeno delay para o servidor iniciar."""
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    print("\n" + "=" * 60)
    print("  🌱 AI Farm Agent — Iniciando...")
    print(f"  📡 Servidor: http://{HOST}:{PORT}")
    print("  🔑 API Key: ...{}".format(api_key[-8:]))
    print("=" * 60 + "\n")

    # Importa servidor aqui para garantir que .env já foi carregado
    from ui.server import app, socketio

    # Abre browser em thread separada
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Inicia servidor
    socketio.run(
        app,
        host=HOST,
        port=PORT,
        debug=False,
        allow_unsafe_werkzeug=True,
        log_output=False,
    )


if __name__ == "__main__":
    main()
