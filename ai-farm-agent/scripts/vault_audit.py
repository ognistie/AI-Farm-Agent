"""
Auditoria do segundo cerebro: o que os agentes leem esta certo, atual e sem repeticao?

Olha as tarefas de referencia (30 Tarefas de referencia), que entram no prompt dos
agentes como "caminho que funciona". Marca para retirar:
  obsoleta   ensina um mecanismo aposentado (ver OBSOLETE): o agente copiaria o caminho velho
  vazia      sem secao "Caminho" util (nada para o agente aproveitar)
  duplicada  mesmo pedido que outra nota (fica a mais completa)

Uso:
    python scripts/vault_audit.py              # relatorio (nao mexe em nada)
    python scripts/vault_audit.py --apply      # marca como nao verificadas, preservando fontes
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Mecanismos que o app nao usa mais para estes casos (cada um com o motivo)
OBSOLETE = [
    (re.compile(r"\bLLM fallback\b", re.I), "caminho 'LLM fallback' (sem rota real; o agente planeja sozinho)"),
    (re.compile(r"\bvision_click\b", re.I), "clique por visao (hoje: teclado, rotina ou piloto que le a tela)"),
    (re.compile(r"\brun_command\b[^\n]*ms-settings", re.I), "run_command para Configuracoes (hoje: open_path ms-settings:)"),
    (re.compile(r"\bweb_click\b", re.I), "web_click por seletor (hoje: piloto do navegador)"),
    (re.compile(r"\btype_text\b[^\n]*\bvision\b|\bvision_type\b", re.I), "digitar por visao"),
]
# Rotinas que AINDA usam o mecanismo marcado (enviar mensagem no WhatsApp/Teams: clique por visao
# no contato). A nota descreve o que o app faz hoje — fica.
CURRENT = {"013 - Ligação no Teams", "014 - Mensagem no WhatsApp"}


def _actions() -> set[str]:
    """Acoes que o motor executa hoje (core/automation.py) + rotas de agente."""
    src = (ROOT / "core" / "automation.py").read_text(encoding="utf-8")
    acts = set(re.findall(r'"([a-z_]+)":self\._', src))
    return acts | {"rotina", "piloto", "routine"}


def _norm(t: str) -> set[str]:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    stop = {"de", "do", "da", "o", "a", "e", "no", "na", "um", "uma", "com", "para", "em", "os", "as"}
    return {w for w in re.findall(r"[a-z0-9]+", t) if w not in stop and not w.isdigit()}


def _section(md: str, title: str) -> str:
    m = re.search(rf"^##\s+{re.escape(title)}\s*\n(.*?)(?=^##\s|\Z)", md, re.M | re.S)
    return m.group(1).strip() if m else ""


def audit(vault: Path) -> list[dict]:
    notes = []
    for f in sorted((vault / "30 Tarefas de referencia").rglob("*.md")):
        md = f.read_text(encoding="utf-8")
        if "tipo: tarefa-referencia" not in md:
            continue                                   # indice/MOC da pasta, nao e referencia
        ask = re.search(r">\s*(?:\[!route\][^\n]*\n>\s*)?([^\n\[]+)", md.split("## Caminho")[0].split("Pedido exemplo", 1)[-1])
        notes.append({"file": f, "rel": f.relative_to(vault).as_posix(), "md": md,
                      "path": _section(md, "Caminho"),
                      "key": _norm(re.sub(r"^\d+\s*-\s*", "", f.stem) + " " + (ask.group(1) if ask else ""))})
    out = []
    acts = _actions()
    for n in notes:
        why = [] if n["file"].stem in CURRENT else [msg for rx, msg in OBSOLETE if rx.search(n["path"])]
        words = set(re.findall(r"[a-z_]+", n["path"].lower()))
        clicks = re.search(r"^agente:\s*(DESKTOP|WEB)\b", n["md"], re.M)
        if len(n["path"]) < 12:
            why.append("sem caminho util (vazia)")
        elif clicks and not (words & acts) and "→" not in n["path"] and "(" not in n["path"]:
            # Desktop/Web executam ACOES no PC: caminho sem nenhuma acao conhecida nao ensina nada
            # (Code/Data/File descrevem o metodo do codigo e ficam)
            why.append("sem caminho util (nenhuma acao que o app execute)")
        n["why"] = why
    # duplicatas: mesmo pedido (titulo + exemplo quase iguais); fica a nota mais completa e sem problema
    for i, a in enumerate(notes):
        for b in notes[i + 1:]:
            if not a["key"] or not b["key"]:
                continue
            j = len(a["key"] & b["key"]) / len(a["key"] | b["key"])
            if j >= 0.75:
                worse = min((a, b), key=lambda n: (not n["why"], len(n["md"])))
                better = b if worse is a else a
                if not any(w.startswith("duplicada") for w in worse["why"]):
                    worse["why"].append(f"duplicada de '{better['file'].stem}'")
    for n in notes:
        if n["why"]:
            out.append(n)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    from core.brain import get_brain
    vault = get_brain().root
    total = len(list((vault / "30 Tarefas de referencia").rglob("*.md")))
    flagged = audit(vault)
    print(f"{len(flagged)} de {total} tarefas de referencia marcadas para retirar\n")
    for n in flagged:
        print(f"- {n['rel']}: {'; '.join(n['why'])}")
    if args.apply and flagged:
        from core.memory_gate import _set_fields
        for n in flagged:
            n["file"].write_text(_set_fields(n["md"], {"verificado": "nao",
                                    "auditoria": "; ".join(n["why"])}), encoding="utf-8")
        print("\nReferencias marcadas como nao verificadas; nenhuma fonte removida.")


if __name__ == "__main__":
    main()
