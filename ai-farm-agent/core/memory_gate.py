"""
Porteiro do segundo cerebro: so memoria VERIFICADA orienta os agentes.

Tipos (inspirado em CoALA/MemGuard, adaptado ao vault):
  procedimento  30 Tarefas de referencia — "como fazer"; entra no prompt SO com verificado: sim
  restricao     60 Aprendizados (licoes) — "o que nao fazer"; curado
  vocabulario   70 Dicionario — como o usuario fala; curado
  registro      40 Execucoes — o que aconteceu; nunca entra no prompt (core/brain.py)
  hipotese      referencia nunca comprovada — permanece no vault, fora da recuperacao

Ciclo de vida: somente evidencia independente que identifica a referencia pode atualizar
seu resultado. Similaridade lexical e agente compativel sao filtros adicionais, nunca prova.
Execucao simulada ou sem evidencia nao conta. Falhas >= 2 e superiores a sucessos rebaixam
o procedimento. Notas retiradas pela curadoria nao retornam do arquivo antigo, mesmo com
contagens historicas. O manifesto versionado registra origem, motivo e substituto.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

MATCH = 0.3
REFS = "30 Tarefas de referencia"
ARCHIVE = Path(__file__).resolve().parent.parent / "memory" / "vault_arquivo" / "hipoteses"
HISTORY = Path(__file__).resolve().parent.parent / "desktop" / "data" / "history.jsonl"


def _evidence_notes(entry):
    """Only an independent verifier identifying the procedure can promote it.

    Generic task success, model done and lexical similarity are not procedure evidence.
    """
    return {item['note'] for item in entry.get('reference_evidence', [])
            if isinstance(item, dict) and isinstance(item.get('note'), str)
            and item.get('verified') is True and item.get('verifier') in ('filesystem', 'uia', 'human')}


def _fm_fields(md: str) -> tuple[dict, str, str]:
    """(campos, bloco frontmatter cru, corpo)."""
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if not m:
        return {}, "", md
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields, m.group(1), md[m.end():]


def _set_fields(md: str, updates: dict) -> str:
    fields, raw, body = _fm_fields(md)
    lines = raw.splitlines() if raw else []
    for k, v in updates.items():
        for i, line in enumerate(lines):
            if line.split(":", 1)[0].strip() == k:
                lines[i] = f"{k}: {v}"
                break
        else:
            lines.append(f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def _note_key(path: Path, md: str) -> tuple[set, str]:
    from core.brain import _tokens
    f, _, _ = _fm_fields(md)
    agent = (f.get("agente") or "").upper().split(",")[0].strip()
    return _tokens(path.stem + " " + f.get("keywords", "") + " " + f.get("tarefa", "")), agent


def _matches(task_tokens: set, agents: set, key: tuple[set, str]) -> bool:
    have, agent = key
    if not task_tokens or not have:
        return False
    j = len(task_tokens & have) / len(task_tokens | have)
    return j >= MATCH and (not agent or agent in agents)


def _run_key(entry: dict) -> tuple[set, set]:
    from core.brain import _tokens
    agents = {(s.get("agent") or "").upper() for s in entry.get("subtasks") or [] if s.get("agent")}
    return _tokens(entry.get("resolved") or entry.get("task") or ""), agents


def _ref_notes(base: Path, excluded=frozenset()) -> list[Path]:
    out = []
    for f in sorted(base.rglob("*.md")) if base.is_dir() else []:
        if f.relative_to(base).as_posix() in excluded:
            continue
        md = f.read_text(encoding="utf-8")
        if _fm_fields(md)[0].get('estado') in ('retirado', 'planejado', 'experimental'):
            continue
        if "tipo: tarefa-referencia" in md[:400]:
            out.append(f)
    return out


# ── verificacao completa (historico inteiro) ──────────────────────────
def verify_all(vault: Path, history: Path = HISTORY, apply: bool = False, archive: Path = ARCHIVE) -> dict:
    """Atualiza evidencia sem remover fontes. Historico ausente/vazio nao revoga curadoria.

    Notas sem correspondencia permanecem intactas; arquivos antigos nunca sao apagados.
    """
    from core.vault_curation import retired_reference_paths
    excluded = retired_reference_paths(vault)
    runs = []
    for line in history.read_text(encoding="utf-8").splitlines() if history.is_file() else []:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("dry_run") or not r.get("subtasks"):
            continue
        toks, agents = _run_key(r)
        runs.append((toks, agents, bool(r.get("success")), (r.get("started_at") or "")[:10], _evidence_notes(r)))
    report = {"verificadas": [], "rebaixadas": [], "hipoteses": [], "restauradas": []}
    candidates = [(f, vault / REFS) for f in _ref_notes(vault / REFS, excluded)] + \
                 [(f, archive) for f in _ref_notes(archive, excluded)]
    for f, base in candidates:
        md = f.read_text(encoding="utf-8")
        if base == archive and (vault / REFS / f.relative_to(base)).exists():
            continue  # a copia no vault e a fonte atual; nao sobrescrever com arquivo antigo
        key = _note_key(f, md)
        ok = fail = 0
        last = ""
        for toks, agents, succ, day, evidence in runs:
            if (f.relative_to(base).as_posix() in evidence or (REFS + '/' + f.relative_to(base).as_posix()) in evidence) and _matches(toks, agents, key):
                if succ:
                    ok, last = ok + 1, max(last, day)
                else:
                    fail += 1
        rel = f.relative_to(base).as_posix()
        demoted = fail >= 2 and fail > ok
        status = "sim" if ok >= 1 and not demoted else "nao"
        if not (ok or fail):
            status = _fm_fields(md)[0].get("verificado", "nao")
        bucket = "verificadas" if status == "sim" else ("rebaixadas" if ok else "hipoteses")
        in_vault = base != archive
        if status == "sim" and not in_vault:
            bucket = "restauradas"
        report[bucket].append({"nota": rel, "sucessos": ok, "falhas": fail, "ultima": last})
        if not apply or not (ok or fail):
            continue
        md = _set_fields(md, {"verificado": status, "sucessos": ok, "falhas": fail,
                              "ultima_execucao": last or "-"})
        if status == "sim":
            dest = vault / REFS / rel
        else:
            dest = f  # hipotese fica versionavel; o filtro verificado controla a recuperacao
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(md, encoding="utf-8")
    return report


# ── a cada execucao (chamado pelo Brain.finish) ───────────────────────
def record_outcome(vault: Path, entry: dict, archive: Path = ARCHIVE) -> Optional[str]:
    """Atualiza a referencia que bate com esta execucao. Devolve o que mudou (para log)."""
    if entry.get("dry_run") or not entry.get("subtasks"):
        return None
    evidence = _evidence_notes(entry)
    if not evidence:
        return None
    from core.vault_curation import retired_reference_paths
    excluded = retired_reference_paths(vault)
    toks, agents = _run_key(entry)
    ok = bool(entry.get("success"))
    day = (entry.get("started_at") or "")[:10]
    best = None
    for base in (vault / REFS, archive):
        for f in _ref_notes(base, excluded):
            if base == archive and (vault / REFS / f.relative_to(base)).exists():
                continue
            md = f.read_text(encoding="utf-8")
            rel = f.relative_to(base).as_posix()
            if rel not in evidence and (REFS + '/' + rel) not in evidence:
                continue
            key = _note_key(f, md)
            if not _matches(toks, agents, key):
                continue
            score = len(toks & key[0]) / len(toks | key[0])
            if best is None or score > best[0]:
                best = (score, f, base, md)
    if best is None:
        return None
    _, f, base, md = best
    fields, _, _ = _fm_fields(md)
    sucessos = int(fields.get("sucessos") or 0) + (1 if ok else 0)
    falhas = int(fields.get("falhas") or 0) + (0 if ok else 1)
    demoted = falhas >= 2 and falhas > sucessos
    status = "sim" if sucessos >= 1 and not demoted else "nao"
    md = _set_fields(md, {"verificado": status, "sucessos": sucessos, "falhas": falhas,
                          "ultima_execucao": day if ok else (fields.get("ultima_execucao") or "-")})
    rel = f.relative_to(base).as_posix()
    if base == archive and status == "sim":
        dest = vault / REFS / rel                    # hipotese comprovada: volta ao vault
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(md, encoding="utf-8")
        return f"promovida: {rel}"
    f.write_text(md, encoding="utf-8")
    if demoted:
        return f"rebaixada: {rel} ({falhas} falhas)"
    return f"{'sucesso' if ok else 'falha'} +1: {rel}"


def restore_references(vault: Path, archive: Path = ARCHIVE) -> list[str]:
    """Copia referencias do arquivo antigo sem apagar originais nem substituir curadoria.

    Operacao explicita e idempotente; nao presume que a nota arquivada foi verificada.
    """
    from core.vault_curation import retired_reference_paths
    restored = []
    for source in _ref_notes(archive, retired_reference_paths(vault)):
        rel = source.relative_to(archive)
        content = source.read_text(encoding="utf-8")
        dest = vault / REFS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with dest.open("x", encoding="utf-8") as out:
                out.write(content)
        except FileExistsError:
            continue
        restored.append(rel.as_posix())
    return restored


def routing_map(vault: Path) -> str:
    """Nota '00 Maestro/Mapa de roteamento': intencao -> agente -> playbooks verificados."""
    from core.brain import _frontmatter
    by_agent: dict[str, list] = {}
    for f in _ref_notes(vault / REFS):
        fm = _frontmatter(f.read_text(encoding="utf-8"))
        if fm.get("verificado") != "sim":
            continue
        a = (fm.get("agente") or "?").upper().split(",")[0].strip()
        by_agent.setdefault(a, []).append((int(fm.get("sucessos") or 0), f.stem))
    intents = {
        "WEB": "abrir site, pesquisar, ler e agir numa página (piloto do navegador)",
        "DESKTOP": "abrir e operar apps do Windows (rotina; piloto do app para o resto)",
        "CODE": "criar ou mudar site, script, projeto",
        "DATA": "criar planilha com dados, fórmulas e gráfico",
        "FILE": "organizar, mover, encontrar arquivos e pastas",
    }
    lines = ["---", "tipo: mapa", "tags: [maestro, roteamento]", "---",
             "# Mapa de roteamento", "",
             "Gerado pelo app a partir das execuções reais (`scripts/brain_verify.py`). Só aparecem",
             "caminhos **verificados** — que já deram certo de verdade no seu PC. É o que os agentes",
             "recebem como referência; hipóteses ficam no vault, fora da recuperação.", "",
             "Antes do Maestro, sem IA: **abrir app/site** (dicionário), **ação no que está aberto**",
             "(direto ao agente) e **pergunta sobre arquivo criado** (lê o arquivo).", ""]
    for agent in ("WEB", "DESKTOP", "CODE", "DATA", "FILE"):
        lines.append(f"## {agent} — {intents[agent]}")
        notes = sorted(by_agent.get(agent, []), reverse=True)
        lines += [f"- [[{stem}]] · {n} sucesso(s)" for n, stem in notes] or ["- (nenhum caminho verificado ainda)"]
        lines.append("")
    return "\n".join(lines)
