"""
Workflow Store v6 — memoria de ROTAS, nao de conteudo.

O que mudou em relacao a v5 (e por que):

- v5 salvava a lista de *resultados* da execucao ("✅ Bloco de Notas",
  "⏳ 3s") e o Maestro usava o match como ATALHO: devolvia so o primeiro
  agente, sem params, sem chamar o LLM. Consequencias: tarefas com 2+
  subtasks perdiam etapas, e pedidos parecidos saiam sempre iguais.
- v6 guarda a ROTA que funcionou: sequencia de agentes + tipo de acao +
  app + nomes dos params (nunca os valores — texto, mensagem, query,
  tema). O Maestro recebe as rotas como REFERENCIA e continua gerando o
  plano do zero para a tarefa atual. Memoria ajuda a rotear; o conteudo
  e sempre novo.
- Upsert por tarefa normalizada: repetir a mesma tarefa incrementa
  contadores em vez de criar um arquivo novo por execucao.
- Falhas tambem sao registradas: rota que falha mais do que funciona
  deixa de ser sugerida.
- Caminho absoluto (antes dependia do diretorio de onde o app era aberto).
- Limite de entradas com despejo das menos usadas.
"""

import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parent / "workflows"
QUARANTINE_DIR = WORKFLOWS_DIR / ".corrupted"

# v6: formato de rota. Arquivos com versao menor sao ignorados no lookup
# (v5 e anteriores guardavam resultados, nao rotas).
CURRENT_VALIDATOR_VERSION = 6

MAX_AGE_DAYS_DEFAULT = 30      # sem uso ha mais tempo = nao sugere
MAX_ENTRIES = 300              # acima disso, despeja as menos usadas
MIN_SCORE = 0.34               # similaridade minima para sugerir

# Params cujo NOME ajuda a rotear, mas cujo VALOR e conteudo do usuario.
# O valor nunca e salvo — so a lista de nomes.
_ROUTING_PARAMS = ("app", "action_type")

_quarantine_logged_once = False


# ───────────────────────────────────────────────────────────────────
#  Normalizacao
# ───────────────────────────────────────────────────────────────────

def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _strip_accents((text or "").lower()))


def _normalize_task(text: str) -> str:
    return " ".join(_tokens(text))


def _task_key(text: str) -> str:
    return hashlib.sha1(_normalize_task(text).encode("utf-8")).hexdigest()[:16]


# ───────────────────────────────────────────────────────────────────
#  Rotas
# ───────────────────────────────────────────────────────────────────

def extract_route(subtasks: list) -> list[dict]:
    """
    Reduz as subtasks do Maestro a uma rota sem conteudo:
    [{"agent": "WEB", "action_type": "search", "app": "", "param_keys": [...]}]
    """
    route = []
    for sub in subtasks or []:
        params = sub.get("params") or {}
        step = {"agent": (sub.get("agent") or "").upper()}
        for key in _ROUTING_PARAMS:
            value = params.get(key)
            if isinstance(value, str) and value.strip():
                step[key] = value.strip().lower()[:40]
        keys = sorted(k for k, v in params.items() if v not in ("", None, [], {}))
        if keys:
            step["param_keys"] = keys
        if sub.get("depends_on") is not None:
            step["depends_on"] = sub.get("depends_on")
        route.append(step)
    return route


def format_route(route: list[dict]) -> str:
    """'WEB(search) -> DESKTOP(teams/send_message)'"""
    parts = []
    for step in route:
        detail = "/".join(v for v in (step.get("app"), step.get("action_type")) if v)
        parts.append(f"{step.get('agent', '?')}({detail})" if detail else step.get("agent", "?"))
    return " -> ".join(parts)


# ───────────────────────────────────────────────────────────────────
#  IO
# ───────────────────────────────────────────────────────────────────

def _quarantine(file_path: Path, reason: str) -> None:
    """Move arquivo corrompido para .corrupted/ — evita re-tentar em todo turno."""
    global _quarantine_logged_once
    try:
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        target = QUARANTINE_DIR / file_path.name
        if target.exists():
            ts = datetime.now().strftime("%H%M%S")
            target = QUARANTINE_DIR / f"{file_path.stem}_{ts}{file_path.suffix}"
        shutil.move(str(file_path), str(target))
        if not _quarantine_logged_once:
            print(f"[workflow_store] quarentena ativa: {QUARANTINE_DIR} ({reason[:60]})")
            _quarantine_logged_once = True
    except OSError as move_err:
        if not _quarantine_logged_once:
            print(f"[workflow_store] nao consegui mover {file_path.name} para quarentena: {move_err}")
            _quarantine_logged_once = True


def _write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _iter_entries():
    """(path, entry) de todos os workflows v6 legiveis."""
    if not WORKFLOWS_DIR.exists():
        return
    for f in WORKFLOWS_DIR.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fh:
                wf = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            _quarantine(f, str(e))
            continue
        if not isinstance(wf, dict):
            _quarantine(f, "nao e objeto JSON")
            continue
        if wf.get("validator_version", 0) < CURRENT_VALIDATOR_VERSION:
            continue
        yield f, wf


def _parse_dt(value):
    try:
        return datetime.fromisoformat(value) if value else None
    except ValueError:
        return None


# ───────────────────────────────────────────────────────────────────
#  API publica
# ───────────────────────────────────────────────────────────────────

def record_outcome(task_description: str, subtasks: list, success: bool) -> dict:
    """
    Registra o resultado de uma execucao (sucesso OU falha).
    Upsert pela tarefa normalizada — a mesma tarefa vira 1 arquivo.
    """
    route = extract_route(subtasks)
    if not route:
        return {}

    now = datetime.now().isoformat(timespec="seconds")
    path = WORKFLOWS_DIR / f"wf_{_task_key(task_description)}.json"

    entry = None
    if path.exists():
        try:
            with open(path, encoding="utf-8") as fh:
                entry = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            _quarantine(path, str(e))
            entry = None

    if not entry or entry.get("validator_version", 0) < CURRENT_VALIDATOR_VERSION:
        entry = {
            "task": task_description,
            "created_at": now,
            "success_count": 0,
            "fail_count": 0,
            "validator_version": CURRENT_VALIDATOR_VERSION,
        }

    entry["route"] = route if success else entry.get("route", route)
    entry["agent"] = route[0]["agent"]
    entry["tags"] = sorted(_extract_tags(task_description))
    entry["topic"] = sorted(_extract_topic_words(task_description))
    entry["last_used"] = now
    if success:
        entry["success_count"] = entry.get("success_count", 0) + 1
    else:
        entry["fail_count"] = entry.get("fail_count", 0) + 1

    _write_atomic(path, entry)
    _evict_if_needed()
    return entry


def save_workflow(task_description, subtasks, agent=None, success=True):
    """Compat v5: agora grava a rota das subtasks (agent e ignorado)."""
    if not isinstance(subtasks, list) or not subtasks or not isinstance(subtasks[0], dict):
        return {}
    return record_outcome(task_description, subtasks, success)


def _similarity(task_tags: set, task_topic: set, task_tokens: set, wf: dict) -> float:
    """
    0..1 — mistura de tags tecnicas, tema e vocabulario geral.

    Nao ha mais filtro "anti cross-topic" (v4/v5): a rota nao carrega
    conteudo, entao reaproveitar a rota de "site sobre budismo" para
    "site sobre muay thai" e seguro — o tema sai sempre da tarefa atual.
    """
    wf_tags = set(wf.get("tags", []))
    wf_topic = set(wf.get("topic", []))
    wf_tokens = set(_tokens(wf.get("task", "")))

    def jaccard(a, b):
        return len(a & b) / len(a | b) if (a | b) else 0.0

    return (0.5 * jaccard(task_tags, wf_tags)
            + 0.3 * jaccard(task_topic, wf_topic)
            + 0.2 * jaccard(task_tokens, wf_tokens))


def find_similar_routes(task_description: str, k: int = 2,
                        max_age_days: int = MAX_AGE_DAYS_DEFAULT) -> list[dict]:
    """
    Ate `k` rotas que ja funcionaram para tarefas parecidas, da mais
    parecida para a menos. Cada item: {task, route, success_count, score}.
    Rotas que falham mais do que funcionam sao ignoradas.
    """
    task_tags = _extract_tags(task_description)
    task_topic = _extract_topic_words(task_description)
    task_tokens = set(_tokens(task_description))
    cutoff = datetime.now() - timedelta(days=max_age_days)

    scored = []
    for _path, wf in _iter_entries():
        if wf.get("cold"):
            continue
        last = _parse_dt(wf.get("last_used") or wf.get("created_at"))
        if not last or last < cutoff:
            continue
        if wf.get("success_count", 0) <= wf.get("fail_count", 0):
            continue
        if not wf.get("route"):
            continue
        score = _similarity(task_tags, task_topic, task_tokens, wf)
        if score >= MIN_SCORE:
            scored.append((score, wf))

    scored.sort(key=lambda x: (x[0], x[1].get("success_count", 0)), reverse=True)

    results, seen_routes = [], set()
    for score, wf in scored:
        signature = format_route(wf["route"])
        if signature in seen_routes:
            continue  # duas tarefas com a mesma rota nao agregam informacao
        seen_routes.add(signature)
        results.append({
            "task": wf.get("task", ""),
            "route": wf["route"],
            "agent": wf.get("agent", ""),
            "tags": wf.get("tags", []),
            "success_count": wf.get("success_count", 0),
            "score": round(score, 3),
        })
        if len(results) >= k:
            break
    return results


def find_similar_workflow(task_description, max_age_days=MAX_AGE_DAYS_DEFAULT):
    """Compat: a rota mais parecida, ou None."""
    found = find_similar_routes(task_description, k=1, max_age_days=max_age_days)
    return found[0] if found else None


def _evict_if_needed() -> None:
    entries = list(_iter_entries())
    if len(entries) <= MAX_ENTRIES:
        return
    entries.sort(key=lambda pe: (pe[1].get("success_count", 0) - pe[1].get("fail_count", 0),
                                 pe[1].get("last_used", "")))
    for path, _wf in entries[:len(entries) - MAX_ENTRIES]:
        try:
            path.unlink()
        except OSError:
            pass


def stats() -> dict:
    """Resumo da memoria para diagnostico."""
    total = legacy = healthy = failing = 0
    if WORKFLOWS_DIR.exists():
        for f in WORKFLOWS_DIR.glob("*.json"):
            total += 1
            try:
                wf = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if wf.get("validator_version", 0) < CURRENT_VALIDATOR_VERSION:
                legacy += 1
            elif wf.get("success_count", 0) > wf.get("fail_count", 0):
                healthy += 1
            else:
                failing += 1
    return {"total": total, "legacy": legacy, "healthy": healthy, "failing": failing}


# ───────────────────────────────────────────────────────────────────
#  Tags e tema
# ───────────────────────────────────────────────────────────────────

_TECH_KEYWORDS = {
    "planilha","excel","grafico","dados","teams","mensagem","chat","enviar",
    "browser","google","youtube","pesquisar","pesquise","pesquisa","site","codigo",
    "python","javascript","criar","arquivo","pasta","mover","copiar","vscode",
    "terminal","projeto","email","outlook","word","documento","abrir","notepad",
    "bloco","notas","whatsapp","paint","calculadora","spotify","explorer",
    "html","css","js","react","vue","flask","fastapi","django","sqlite",
    "dashboard","crud","login","admin","landing","portfolio",
    "code","studio","visual","editor","ide","vim","emacs","sublime","atom",
    "sistema","aplicativo","aplicacao","app","plataforma","gerenciador",
    "controle","programa","script","servico","servidor","cliente","api",
}

# Sinonimos -> forma canonica usada nas tags
_TAG_ALIASES = {
    "abra": "abrir", "abre": "abrir", "crie": "criar", "cria": "criar",
    "envie": "enviar", "envia": "enviar", "manda": "enviar", "mande": "enviar",
    "pesquise": "pesquisar", "pesquisa": "pesquisar", "busque": "pesquisar",
    "procure": "pesquisar", "planilhas": "planilha", "arquivos": "arquivo",
    "pastas": "pasta", "mensagens": "mensagem",
}

_STOPWORDS_TOPIC = {
    "abra","abrir","abre","crie","criar","cria","faca","fazer","faz",
    "quero","gostaria","favor","sobre","para","pelo","pela",
    "como","onde","quando","tambem","sendo","muito","mais","menos",
    "porem","ainda","apenas","somente","seja","seria","esta","estao",
    "isso","aquilo","esse","essa","aquele","aquela","este",
    "professional","profissional","completo","completa","novo","nova",
    "umm","uma","uns","umas","dois","duas","tres","tudo","todos","todas",
    "historia","origem","origens","suas","seus","minha","minhas",
    "depois","antes","entao","agora","hoje","ontem","amanha","sempre",
    "envie","envia","manda","mande","pesquise","busque","procure","outro","outra",
    "planilhas","arquivos","pastas","mensagens","contendo","com","sem",
}


def _extract_tags(text):
    tags = set()
    for tok in _tokens(text):
        tok = _TAG_ALIASES.get(tok, tok)
        if tok in _TECH_KEYWORDS:
            tags.add(tok)
    return tags


def _extract_topic_words(text):
    """
    Palavras do TEMA: 4+ letras que nao sao tecnicas nem funcionais.
    'site sobre muay thai' -> {'muay','thai'}.
    """
    return {
        w for w in _tokens(text)
        if len(w) >= 4 and not w.isdigit()
        and w not in _TECH_KEYWORDS and w not in _STOPWORDS_TOPIC
        and _TAG_ALIASES.get(w, w) not in _TECH_KEYWORDS
    }
