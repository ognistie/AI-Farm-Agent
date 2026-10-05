"""
Avaliacao de conversas — como o agente se sai em situacoes variadas, SEM executar nada.

Cada cenario monta o estado da conversa (o que ja foi dito e o que esta aberto),
faz o pedido e confere o caminho inteiro que o app faria:
  resolvedor (continua ou e novo? em qual alvo?) -> Maestro (qual agente?) ->
  alvo de continuacao (core/routing.py) -> plano do agente (quais acoes?) -> politicas.

Usa o modelo de verdade (custa centavos) e o MESMO codigo do app; so nao executa
os passos. Rodar:
    python scripts/eval_conversations.py            # todos
    python scripts/eval_conversations.py excel      # so os que tem 'excel' no nome
    python scripts/eval_conversations.py --vault    # grava o relatorio no Obsidian
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT.parent / ".env")
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


# ── estados de partida ───────────────────────────────────────────────
def nothing(s):
    pass


def settings_open(s):
    s.add_turn("abre as configurações do windows", "abrir Configurações do Windows", "new", ["DESKTOP"], True,
               "Configurações abertas")
    s.remember_app("configuracoes", 0, "Configurações")


def excel_open(s):
    s.add_turn("abre o excel", "abrir o Excel", "new", ["DESKTOP"], True, "Excel aberto em Pasta1")
    s.remember_app("excel", 0, "Pasta1 - Excel")


def notepad_open(s):
    s.add_turn("abre o bloco de notas", "abrir o Bloco de Notas", "new", ["DESKTOP"], True, "Bloco de Notas aberto")
    s.remember_app("notepad", 0, "Sem título - Bloco de notas")


def calc_open(s):
    s.add_turn("abre a calculadora", "abrir a Calculadora", "new", ["DESKTOP"], True, "Calculadora aberta")
    s.remember_app("calculadora", 0, "Calculadora")


def youtube_open(s):
    s.add_turn("abre o youtube e pesquisa lofi", "abrir o YouTube e pesquisar lofi", "new", ["WEB"], True,
               "Resultados de lofi no YouTube")
    s.remember_web(0, "https://www.youtube.com/results?search_query=lofi", "lofi - YouTube",
                   ['1. link "Lofi Girl - beats to relax"', '2. link "Study Session 1 hour"', '3. link "Rainy lofi"'])


def shop_open(s):
    s.add_turn("pesquisa fone bluetooth no mercado livre", "pesquisar fone bluetooth no Mercado Livre", "new",
               ["WEB"], True, "Resultados do Mercado Livre: 1) JBL Tune R$ 199 2) Redmi Buds R$ 158")
    s.remember_web(0, "https://lista.mercadolivre.com.br/fone-bluetooth", "Fone Bluetooth | MercadoLivre",
                   ['1. link "Fone JBL Tune 520BT"', '2. link "Redmi Buds 6 Active"', '3. link "Fone QCY T13"'])


_PROJECT = None


def code_open(s):
    global _PROJECT
    if _PROJECT is None:
        _PROJECT = tempfile.mkdtemp(prefix="eval_site_")
        Path(_PROJECT, "index.html").write_text(
            '<!doctype html><html><head><link rel="stylesheet" href="style.css"></head>'
            '<body><h1 class="titulo">Floricultura</h1><button>Comprar</button></body></html>', encoding="utf-8")
        Path(_PROJECT, "style.css").write_text(".titulo{color:green} button{border-radius:4px}", encoding="utf-8")
    s.add_turn("faz um site de floricultura", "criar site de floricultura", "new", ["CODE"], True, "Site criado")
    s.remember_code(_PROJECT, ["index.html", "style.css"])


def downloads_open(s):
    s.add_turn("abre a pasta downloads", "abrir a pasta Downloads", "new", ["FILE"], True, "Downloads aberta")
    s.remember_folder(os.path.join(os.path.expanduser("~"), "Downloads"))


# ── cenarios ─────────────────────────────────────────────────────────
# expect: kind (set) | target | agents (subconjunto esperado) | any (alguma acao) | none (proibidas)
#         approved (plano aprovado) | answer (texto contem)
SCENARIOS = [
    ("config: clica em sistema", settings_open, "clica em sistema",
     {"kind": {"continue"}, "target": "app:configuracoes", "any": {"app_task"}, "none": {"app_search"}}),
    ("config: entra em acessibilidade", settings_open, "agora entra em acessibilidade",
     {"kind": {"continue"}, "any": {"app_task", "open_path"}, "none": {"app_search"}}),
    ("config: ativa o modo escuro", settings_open, "ativa o modo escuro",
     {"kind": {"continue", "new"}, "any": {"app_task"}}),
    ("config: volta", settings_open, "volta pra página anterior",
     {"kind": {"continue"}, "any": {"app_task"}}),
    ("excel: abre o excel (ja aberto)", excel_open, "abre o excel",
     {"kind": {"continue", "new"}, "any": {"focus_window"}, "none": {"app_search", "vision_click"}}),
    ("excel: preenche coluna", excel_open, "preenche a coluna A com os meses do ano",
     {"kind": {"continue"}, "agents": {"DESKTOP"}, "any": {"app_task"}, "none": {"app_search"}, "approved": True}),
    ("excel: alfabeto nas colunas", excel_open, "preencher as colunas A, B e C com as letras do alfabeto",
     {"kind": {"continue"}, "any": {"app_task"}, "none": {"app_search"}, "approved": True}),
    ("excel: abrir e escrever do zero", nothing, "abre o excel e escreve nome, idade e cidade na primeira linha",
     {"any": {"app_task", "excel_write", "run_python"}, "approved": True}),
    ("notepad: abrir e escrever", nothing, "abre o bloco de notas e escreve de 1 até 10",
     {"agents": {"DESKTOP"}, "any": {"blank_document"}, "approved": True}),
    ("notepad: continuar escrevendo", notepad_open, "agora escreve um poema curto sobre o mar",
     {"kind": {"continue"}, "any": {"app_type"}, "none": {"app_search", "blank_document"}, "approved": True}),
    ("notepad: outro bloco de notas", notepad_open, "abre outro bloco de notas",
     {"any": {"app_search"}}),
    ("calc: continuar a conta", calc_open, "agora divide por 4",
     {"kind": {"continue"}, "any": {"app_task"}, "none": {"app_search"}}),
    ("calc: abrir e calcular", nothing, "abre a calculadora e calcula 15 por cento de 200",
     {"any": {"app_task"}, "approved": True}),
    ("youtube: segundo vídeo", youtube_open, "abre o segundo vídeo",
     {"kind": {"continue"}, "target": "web", "any": {"browser_task"}}),
    ("youtube: pula o vídeo", youtube_open, "pula esse vídeo",
     {"kind": {"continue"}, "target": "web", "any": {"browser_task"}}),
    ("youtube: config do windows (app novo)", youtube_open, "abre as configurações do windows",
     {"kind": {"new"}, "any": {"open_path"}, "none": {"browser_task"}}),
    ("youtube: pergunta sobre a lista", youtube_open, "qual era o nome do primeiro vídeo?",
     {"kind": {"question", "continue"}}),
    ("youtube: outra pesquisa", youtube_open, "pesquisa no google a previsão do tempo pra hoje",
     {"agents": {"WEB"}}),
    ("loja: preço do segundo", shop_open, "e o segundo, quanto custa?",
     {"kind": {"question", "continue"}}),
    ("code: muda a cor do título", code_open, "muda a cor do título pra vermelho",
     {"kind": {"continue"}, "target": "code", "any": {"edit_project"}}),
    ("code: desfaz", code_open, "desfaz", {"kind": {"undo"}}),
    ("code: troque algumas coisas", code_open, "troque algumas coisas", {"kind": {"clarify"}}),
    ("pasta: organiza essa pasta", downloads_open, "organiza essa pasta por tipo de arquivo",
     {"agents": {"FILE"}, "approved": True}),
    ("geral: abrir vs code", nothing, "abrir vs code", {"agents": {"DESKTOP", "CODE"}}),
    ("notepad: fecha esse", notepad_open, "fecha esse bloco de notas",
     {"none": {"close_app"}}),
    ("youtube: e o terceiro?", youtube_open, "e o terceiro?", {"kind": {"continue", "question"}}),
    ("papo: valeu (texto)", youtube_open, "valeu, era isso", {"none": {"browser_task", "app_task", "run_python"}}),
    ("excel: salva a planilha", excel_open, "salva essa planilha como vendas", {"kind": {"continue"}, "any": {"app_task"}}),
]


def run_one(name, setup, say, exp, agents, maestro):
    from core.session import Session
    from core.followup import resolve
    from core.routing import continue_target_for
    from core.plan_validator import validate_steps
    s = Session()
    setup(s)
    t0 = time.time()
    out = {"name": name, "say": say, "kind": "", "target": "", "agents": [], "actions": [], "approved": True,
           "answer": "", "notes": []}
    r = resolve(say, s)
    out.update(kind=r["kind"], target=r.get("target") or "", answer=r.get("answer") or r.get("question") or "")
    if r["kind"] in ("new", "continue"):
        plan = maestro.analyze(r["task"], conversation=s.context_block(), continue_in=r.get("target") or "")
        if plan.get("needs_clarification"):
            out["kind"] = "clarify"
            out["answer"] = plan.get("question", "")
        used = False
        for sub in plan.get("subtasks", []):
            ag = (sub.get("agent") or "").upper()
            out["agents"].append(ag)
            params = dict(sub.get("params") or {})
            tgt, why = continue_target_for(s, ag, params, r.get("target"), r["task"], used)
            if tgt:
                params["continue"] = tgt
                used = used or why == "resolver"
                out["notes"].append(f"{ag} continua em {tgt.get('key') or tgt['type']} ({why})")
            sub["params"] = params
            agent = agents.get(ag)
            if agent is None:
                out["notes"].append(f"agente desconhecido {ag}")
                continue
            payload = {"task": sub.get("task", ""), "params": params, "original_task": sub.get("original_task", "")}
            ctx = params if ag == "DESKTOP" and params.get("app") else None
            try:
                p = agent.plan(payload, context=ctx)
            except Exception as e:
                out["notes"].append(f"{ag} plan falhou: {e}")
                out["approved"] = False
                continue
            steps = p.get("steps") or []
            if p.get("error") or not steps:
                out["approved"] = False
                out["notes"].append(f"{ag} sem passos: {str(p.get('error') or p.get('reason'))[:80]}")
            out["actions"] += [st.get("action") for st in steps]
            v = validate_steps(ag, sub, steps, r["task"])
            if not v.approved:
                out["approved"] = False
                out["notes"].append(f"reprovado: {v.summary()[:100]}")
    out["seconds"] = round(time.time() - t0, 1)

    fails = []
    if "kind" in exp and out["kind"] not in exp["kind"]:
        fails.append(f"kind={out['kind']} (esperado {'/'.join(sorted(exp['kind']))})")
    if "target" in exp and out["target"] != exp["target"]:
        fails.append(f"alvo={out['target'] or '-'} (esperado {exp['target']})")
    if "agents" in exp and not (set(out["agents"]) & exp["agents"]):
        fails.append(f"agentes={out['agents']} (esperado um de {sorted(exp['agents'])})")
    if "any" in exp and not (set(out["actions"]) & exp["any"]):
        fails.append(f"acoes={out['actions']} (esperado alguma de {sorted(exp['any'])})")
    if "none" in exp and set(out["actions"]) & exp["none"]:
        fails.append(f"acao proibida {sorted(set(out['actions']) & exp['none'])}")
    if exp.get("approved") and not out["approved"]:
        fails.append("plano reprovado/vazio")
    out["pass"] = not fails
    out["fails"] = fails
    return out


def main(argv):
    from agents.maestro import Maestro
    from agents.web_agent import WebAgent
    from agents.desktop_agent import DesktopAgent
    from agents.code_agent import CodeAgent
    from agents.file_agent import FileAgent
    from agents.data_agent import DataAgent
    from core.ai_client import get_client
    agents = {"WEB": WebAgent(), "DESKTOP": DesktopAgent(), "CODE": CodeAgent(), "FILE": FileAgent(),
              "DATA": DataAgent()}
    maestro = Maestro()
    flt = [a for a in argv if not a.startswith("--")]
    chosen = [sc for sc in SCENARIOS if not flt or any(f.lower() in sc[0].lower() for f in flt)]
    c0 = get_client().metrics["total_cost_usd"]
    results = []
    for name, setup, say, exp in chosen:
        res = run_one(name, setup, say, exp, agents, maestro)
        results.append(res)
        mark = "OK  " if res["pass"] else "FAIL"
        print(f"{mark} | {name:38} | {res['kind']:9} {res['target'] or '-':18} | "
              f"{','.join(res['agents']) or '-':12} | {','.join(res['actions'])[:60]}")
        for f in res["fails"]:
            print(f"       ✗ {f}")
        for n in res["notes"]:
            print(f"       · {n}")
    ok = sum(r["pass"] for r in results)
    cost = get_client().metrics["total_cost_usd"] - c0
    print(f"\n{ok}/{len(results)} cenarios ok  ·  US$ {cost:.3f}")
    if "--vault" in argv:
        write_report(results, cost)
    return 0 if ok == len(results) else 1


def write_report(results, cost):
    from datetime import date
    from core.brain import get_brain
    lines = ["---", "tipo: avaliacao", "tags: [avaliacao, conversa]", "cssclasses: [agent-maestro]", "---",
             "# 🧪 Avaliação de conversas", "", "← [[Conversa continua]] · [[Modo voz]] · [[Roteiro de testes]]", "",
             f"> [!info] Última rodada: {date.today().isoformat()} — {sum(r['pass'] for r in results)}/"
             f"{len(results)} cenários ok, US$ {cost:.3f}",
             "> Gerado por `scripts/eval_conversations.py --vault` (sem executar nada no PC).", "",
             "| | Cenário | Fala | Entendeu | Alvo | Agentes | Ações | Problema |", "|---|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {'✅' if r['pass'] else '❌'} | {r['name']} | {r['say']} | {r['kind']} | "
                     f"{r['target'] or '-'} | {', '.join(r['agents']) or '-'} | {', '.join(r['actions'])[:60] or '-'} | "
                     f"{'; '.join(r['fails'])[:120] or '-'} |")
    path = get_brain().root / "00 Maestro" / "Avaliacao de conversas.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"relatório: {path}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
