"""
Limpeza pontual dos workflows existentes: aciona a quarentena automatica
do workflow_store.find_similar_workflow para mover todos os JSONs truncados
para memory/workflows/.corrupted/ antes do proximo run normal do sistema.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import memory.workflow_store as ws

before = len(list(ws.WORKFLOWS_DIR.glob("*.json")))
ws.find_similar_workflow("limpeza inicial dos workflows corrompidos")
after = len(list(ws.WORKFLOWS_DIR.glob("*.json")))
corrupted = len(list(ws.QUARANTINE_DIR.glob("*.json"))) if ws.QUARANTINE_DIR.exists() else 0

print(f"workflows/ antes:    {before} arquivo(s)")
print(f"workflows/ depois:   {after} arquivo(s) validos")
print(f".corrupted/:         {corrupted} arquivo(s) movido(s) para quarentena")
