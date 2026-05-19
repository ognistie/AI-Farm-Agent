"""
Workflow Store — Salva e recupera workflows bem-sucedidos.

v3: quarentena de arquivos corrompidos + invalidacao por idade.

- v3: arquivos truncados (legado do bug `set` no json.dump) sao MOVIDOS para
      memory/workflows/.corrupted/ na primeira leitura. Para de spammar log.
- v2: invalidacao por idade (briefing principio 6 — idempotencia).
      Workflows mais velhos que MAX_AGE_DAYS nao sao mais usados diretamente.
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

WORKFLOWS_DIR = Path("memory/workflows")
QUARANTINE_DIR = WORKFLOWS_DIR / ".corrupted"
MAX_AGE_DAYS_DEFAULT = 30
_quarantine_logged_once = False  # silencia depois do primeiro turno


def save_workflow(task_description, steps, agent, success):
    if not success:
        return
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow = {
        "task": task_description,
        "agent": agent,
        "steps": steps,
        "created_at": datetime.now().isoformat(),
        "success_count": 1,
        "tags": list(_extract_tags(task_description)),
    }
    with open(WORKFLOWS_DIR / f"{agent.lower()}_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)


def _quarantine(file_path: Path, reason: str) -> None:
    """Move arquivo corrompido para .corrupted/ — evita re-tentar em todo turno."""
    global _quarantine_logged_once
    try:
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        target = QUARANTINE_DIR / file_path.name
        # se ja existe na quarentena, anexa timestamp
        if target.exists():
            ts = datetime.now().strftime("%H%M%S")
            target = QUARANTINE_DIR / f"{file_path.stem}_{ts}{file_path.suffix}"
        shutil.move(str(file_path), str(target))
        if not _quarantine_logged_once:
            print(f"[workflow_store] quarentena ativa: {QUARANTINE_DIR}")
            _quarantine_logged_once = True
    except OSError as move_err:
        # se nao deu pra mover, ao menos avisa uma vez
        if not _quarantine_logged_once:
            print(f"[workflow_store] nao consegui mover {file_path.name} para quarentena: {move_err}")
            _quarantine_logged_once = True


def find_similar_workflow(task_description, max_age_days=MAX_AGE_DAYS_DEFAULT):
    """
    Encontra workflow similar suficientemente recente.

    Arquivos corrompidos sao movidos para .corrupted/ silenciosamente
    (so loga uma vez por sessao).
    """
    if not WORKFLOWS_DIR.exists():
        return None

    task_tags = _extract_tags(task_description)
    cutoff = datetime.now() - timedelta(days=max_age_days)
    best, best_score = None, 0

    for f in WORKFLOWS_DIR.glob("*.json"):
        # nao processa nada dentro de .corrupted/
        if QUARANTINE_DIR.name in f.parts:
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                wf = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            _quarantine(f, str(e))
            continue

        created = wf.get("created_at", "")
        try:
            created_dt = datetime.fromisoformat(created) if created else None
        except ValueError:
            created_dt = None
        if not created_dt or created_dt < cutoff:
            continue

        common = len(task_tags & set(wf.get("tags", [])))
        if common > best_score:
            best_score = common
            best = wf

    return best if best_score >= 2 else None


def _extract_tags(text):
    keywords = {
        "planilha","excel","grafico","dados","teams","mensagem","chat","enviar",
        "browser","google","pesquisar","site","codigo","python","javascript","criar",
        "arquivo","pasta","mover","copiar","vscode","terminal","projeto",
        "email","outlook","word","documento","abrir","notepad","whatsapp",
        # tech specs ampliam o matching para reuso de workflows similares
        "html","css","js","react","vue","flask","fastapi","django","sqlite",
        "dashboard","crud","login","admin","landing","portfolio",
    }
    return set(text.lower().split()) & keywords
