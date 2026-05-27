"""
Workflow Store — Salva e recupera workflows bem-sucedidos.

v4: filtro cross-topic.
- Match exige overlap tecnico (tags) E overlap tematico (substantivos
  nao-tecnicos com 4+ letras). Sem isso, um workflow antigo de
  "site sobre budismo" casava qualquer "site sobre <X>" e contaminava
  o tema. Agora descarta quando o tema novo e disjunto do antigo.

v3: quarentena de arquivos corrompidos + invalidacao por idade.

- v3: arquivos truncados (legado do bug `set` no json.dump) sao MOVIDOS para
      memory/workflows/.corrupted/ na primeira leitura. Para de spammar log.
- v2: invalidacao por idade (briefing principio 6 — idempotencia).
      Workflows mais velhos que MAX_AGE_DAYS nao sao mais usados diretamente.
"""

import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

WORKFLOWS_DIR = Path("memory/workflows")
QUARANTINE_DIR = WORKFLOWS_DIR / ".corrupted"
MAX_AGE_DAYS_DEFAULT = 30

# v5: incrementar quando o pipeline de validacao mudar. Workflows salvos
# com versao anterior sao IGNORADOS no find (anti-poison).
CURRENT_VALIDATOR_VERSION = 5
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
        "validator_version": CURRENT_VALIDATOR_VERSION,  # v5 anti-poison
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

    Regras de match:
      - overlap tecnico >= 2 (tags em _TECH_KEYWORDS)
      - overlap tematico >= 1 OU ambos os temas vazios (tarefa puramente
        tecnica como "abra o vscode"). Sem isso, um workflow de
        "site sobre budismo" casaria qualquer "site sobre <outro tema>"
        e contaminaria o output.

    Arquivos corrompidos sao movidos para .corrupted/ silenciosamente
    (so loga uma vez por sessao).
    """
    if not WORKFLOWS_DIR.exists():
        return None

    task_tags = _extract_tags(task_description)
    task_topic = _extract_topic_words(task_description)
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

        # v5 ANTI-POISON: workflows salvos antes do validator atual sao
        # IGNORADOS no lookup. Garantia: nunca reaplicar codigo que nao
        # passaria nos validators de hoje (era a causa do bug do Tkinter
        # inline reaparecendo em loop nas tasks novas).
        wf_version = wf.get("validator_version", 0)
        if wf_version < CURRENT_VALIDATOR_VERSION:
            continue

        common = len(task_tags & set(wf.get("tags", [])))
        if common < 2:
            continue

        # Anti cross-topic: descarta match se o tema do workflow antigo
        # nao tem nenhuma palavra em comum com o tema atual. Tarefas
        # puramente tecnicas (sem tema) continuam batendo normalmente.
        wf_topic = _extract_topic_words(wf.get("task", ""))
        if wf_topic and task_topic and not (wf_topic & task_topic):
            continue

        if common > best_score:
            best_score = common
            best = wf

    return best if best_score >= 2 else None


_TECH_KEYWORDS = {
    "planilha","excel","grafico","dados","teams","mensagem","chat","enviar",
    "browser","google","pesquisar","site","codigo","python","javascript","criar",
    "arquivo","pasta","mover","copiar","vscode","terminal","projeto",
    "email","outlook","word","documento","abrir","notepad","whatsapp",
    # tech specs ampliam o matching para reuso de workflows similares
    "html","css","js","react","vue","flask","fastapi","django","sqlite",
    "dashboard","crud","login","admin","landing","portfolio",
    # nomes de editores/aplicativos comuns nao sao tema
    "code","studio","visual","editor","ide","vim","emacs","sublime","atom",
    # substantivos genericos de software que nao caracterizam dominio
    "sistema","aplicativo","aplicacao","app","plataforma","gerenciador",
    "controle","programa","script","servico","servidor","cliente","api",
}

# Palavras funcionais que aparecem em qualquer task e nao caracterizam tema.
_STOPWORDS_TOPIC = {
    "abra","abrir","abre","crie","criar","cria","faca","fazer","faz",
    "fazer","quero","gostaria","favor","sobre","para","pelo","pela",
    "como","onde","quando","tambem","sendo","muito","mais","menos",
    "porem","ainda","apenas","somente","seja","seria","esta","estao",
    "isso","aquilo","esse","essa","aquele","aquela","este","esta",
    "professional","profissional","completo","completa","novo","nova",
    "umm","uma","uns","umas","dois","duas","tres","tudo","todos","todas",
    "historia","história","origem","origens","suas","seus","minha","minhas",
    "depois","antes","entao","agora","hoje","ontem","amanha","sempre",
}


def _extract_tags(text):
    return set(text.lower().split()) & _TECH_KEYWORDS


def _extract_topic_words(text):
    """
    Palavras do TEMA da tarefa: substantivos com 4+ letras que nao sao
    tecnicas nem funcionais. Para 'site sobre muay thai' -> {'muay','thai'}.
    Para 'site sobre budismo' -> {'budismo'}. Esses conjuntos sao usados
    para impedir reuso cross-topic de workflows.
    """
    if not text:
        return set()
    words = re.findall(r"[a-záàâãéêíóôõúüç]{4,}", text.lower())
    return {w for w in words if w not in _TECH_KEYWORDS and w not in _STOPWORDS_TOPIC}
