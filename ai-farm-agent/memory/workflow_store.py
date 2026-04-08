"""
Workflow Store — Salva e recupera workflows bem-sucedidos.
"""

import json
import os
from datetime import datetime
from pathlib import Path

WORKFLOWS_DIR = Path("memory/workflows")

def save_workflow(task_description, steps, agent, success):
    if not success:
        return
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow = {
        "task": task_description, "agent": agent, "steps": steps,
        "created_at": datetime.now().isoformat(), "success_count": 1,
        "tags": _extract_tags(task_description)
    }
    with open(WORKFLOWS_DIR / f"{agent.lower()}_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

def find_similar_workflow(task_description):
    if not WORKFLOWS_DIR.exists():
        return None
    task_tags = _extract_tags(task_description)
    best, best_score = None, 0
    for f in WORKFLOWS_DIR.glob("*.json"):
        try:
            with open(f) as fh:
                wf = json.load(fh)
            common = len(task_tags & set(wf.get("tags", [])))
            if common > best_score:
                best_score = common
                best = wf
        except:
            pass
    return best if best_score >= 2 else None

def _extract_tags(text):
    keywords = {"planilha","excel","grafico","dados","teams","mensagem","chat","enviar",
        "browser","google","pesquisar","site","codigo","python","javascript","criar",
        "arquivo","pasta","mover","copiar","vscode","terminal","projeto",
        "email","outlook","word","documento","abrir","notepad","whatsapp"}
    return set(text.lower().split()) & keywords