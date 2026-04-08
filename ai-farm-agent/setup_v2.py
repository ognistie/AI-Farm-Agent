"""
setup_v2.py — Roda este script na raiz do projeto para criar toda a estrutura v2.
Coloque este arquivo em: ai-farm-agent/ai-farm-agent/setup_v2.py
Rode: python setup_v2.py
"""

import os

# Pastas novas
pastas = [
    "memory",
    "memory/workflows",
    "state_maps",
    "logs",
]

# Arquivos novos (criados vazios como placeholder)
arquivos = [
    # Core novos
    "core/interaction_layer.py",
    "core/uia_driver.py",
    "core/state_machine.py",
    "core/retry_engine.py",
    "core/wait_engine.py",
    "core/ocr_local.py",
    "core/action_logger.py",

    # Agents novos
    "agents/memory_agent.py",

    # Memory
    "memory/__init__.py",
    "memory/workflow_store.py",

    # State maps
    "state_maps/teams.json",
    "state_maps/excel.json",
    "state_maps/vscode.json",
    "state_maps/chrome.json",
    "state_maps/explorer.json",

    # Logs
    "logs/actions.jsonl",
]

print("=" * 50)
print("  AI Farm Agent v2 — Setup de Estrutura")
print("=" * 50)

# Cria pastas
for pasta in pastas:
    os.makedirs(pasta, exist_ok=True)
    print(f"  📁 Pasta criada: {pasta}/")

# Cria arquivos (só se não existem)
criados = 0
existentes = 0
for arquivo in arquivos:
    pasta_do_arquivo = os.path.dirname(arquivo)
    if pasta_do_arquivo:
        os.makedirs(pasta_do_arquivo, exist_ok=True)

    if os.path.exists(arquivo):
        print(f"  ⏭️  Já existe: {arquivo}")
        existentes += 1
    else:
        # Cria com conteúdo mínimo
        if arquivo.endswith(".py"):
            with open(arquivo, "w", encoding="utf-8") as f:
                nome = os.path.basename(arquivo).replace(".py", "")
                f.write(f'"""\n{nome} — Placeholder v2. Substituir pelo código real.\n"""\n')
        elif arquivo.endswith(".json"):
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write("{}\n")
        elif arquivo.endswith(".jsonl"):
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write("")
        print(f"  ✅ Criado: {arquivo}")
        criados += 1

print()
print(f"  Resultado: {criados} criados, {existentes} já existiam")
print()
print("  Próximo passo:")
print("  1. pip install pywinauto easyocr")
print("  2. Substitua os placeholders pelos arquivos reais")
print()
print("=" * 50)
