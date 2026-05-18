"""
Workflow Store — Salva e recupera workflows bem-sucedidos.

v2: invalidacao por idade (briefing principio 6 — idempotencia).
Workflows mais velhos que MAX_AGE_DAYS nao sao mais usados diretamente,
evitando que templates obsoletos sobrevivam mudancas de UI/site/API.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

WORKFLOWS_DIR = Path("memory/workflows")
MAX_AGE_DAYS_DEFAULT = 30  # workflow mais velho que isso = ignorado

def save_workflow(task_description, steps, agent, success):
    if not success:
        return
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow = {
        "task": task_description, "agent": agent, "steps": steps,
        "created_at": datetime.now().isoformat(), "success_count": 1,
        "tags": list(_extract_tags(task_description))
    }
    with open(WORKFLOWS_DIR / f"{agent.lower()}_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

def find_similar_workflow(task_description, max_age_days=MAX_AGE_DAYS_DEFAULT):
    """
    Encontra workflow similar suficientemente recente.

    Args:
      task_description: texto da tarefa atual
      max_age_days: ignora workflows mais antigos que isso (anti-obsolescencia)
    """
    if not WORKFLOWS_DIR.exists():
        return None
    task_tags = _extract_tags(task_description)
    cutoff = datetime.now() - timedelta(days=max_age_days)
    best, best_score = None, 0
    for f in WORKFLOWS_DIR.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fh:
                wf = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[workflow_store] ignorando {f.name}: {e}")
            continue

        # Idade — se nao deu pra parsear, NAO confia no workflow
        created = wf.get("created_at", "")
        try:
            created_dt = datetime.fromisoformat(created) if created else None
        except ValueError:
            created_dt = None
        if not created_dt or created_dt < cutoff:
            continue  # workflow expirado

        common = len(task_tags & set(wf.get("tags", [])))
        if common > best_score:
            best_score = common
            best = wf
    return best if best_score >= 2 else None

def _extract_tags(text):
    keywords = {"planilha","excel","grafico","dados","teams","mensagem","chat","enviar",
        "browser","google","pesquisar","site","codigo","python","javascript","criar",
        "arquivo","pasta","mover","copiar","vscode","terminal","projeto",
        "email","outlook","word","documento","abrir","notepad","whatsapp"}
    return set(text.lower().split()) & keywords