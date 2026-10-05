"""
Avaliacao do entendimento de voz — o que o agente faz com o que o microfone OUVIU.

Cada caso e uma transcricao realista (nomes mal ouvidos, giria, gaguejo,
autocorrecao, ruido de fundo, pergunta, papo) + o estado da conversa. Roda o
MESMO caminho do app (dicionario -> atalho rapido -> modelo) sem executar nada
e confere com regras em codigo:
  kind      o tipo esperado (command | chat | answer | stop | unclear | noise)
  has       grupos "um destes" que o pedido limpo (ou o palpite) precisa conter
  not       palavras que NAO podem aparecer no pedido (palpite inventado)
  reply     grupos que a resposta falada precisa conter (ex.: dado pedido)
  target    alvo de continuacao esperado (quando o entendimento devolve alvo)
Qualidade da fala (todas): curta, sem bordoes roboticos, sem repetir as recentes.

Usa o modelo de verdade (centavos). Rodar:
    python scripts/eval_voice.py               # 2 rodadas de cada caso
    python scripts/eval_voice.py --trials 1 zap
    python scripts/eval_voice.py --vault       # grava o relatorio no Obsidian
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
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

_spec = importlib.util.spec_from_file_location("eval_conversations", ROOT / "scripts" / "eval_conversations.py")
_ec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ec)
nothing, settings_open, excel_open, notepad_open = _ec.nothing, _ec.settings_open, _ec.excel_open, _ec.notepad_open
youtube_open, downloads_open = _ec.youtube_open, _ec.downloads_open

def youtube_offer(s):
    youtube_open(s)
    s.set_last_reply("Achei vídeos de lofi. Quer que eu toque o primeiro?")


CMD = {"command"}
ROBOTIC = re.compile(r"\b(entendido|processando|certamente|tarefa conclu[ií]da|comando recebido|"
                     r"como um modelo|sou uma ia|estou executando a tarefa)\b", re.I)
RECENT = ["Beleza, abrindo o Google.", "Abrindo o YouTube."]

# (nome, estado, ouvido, confianca, esperado)
CASES = [
    # ── nomes mal ouvidos ─────────────────────────────────────────
    ("vs code: google escute", nothing, "abre o google escute", 0.62,
     {"kind": CMD | {"unclear"}, "has": [["vs code", "visual studio"]], "not": ["google"]}),
    ("vs code: so o nome", nothing, "google escute", 0.55,
     {"kind": CMD | {"unclear"}, "has": [["vs code", "visual studio"]]}),
    ("google: gaguejo meu", nothing, "o meu, meu, meu google", 0.7,
     {"kind": CMD | {"unclear"}, "has": [["google"]], "not": ["meu meu"]}),
    ("youtube: iutubi", nothing, "abri o iutubi", 0.66, {"kind": CMD, "has": [["youtube"]]}),
    ("spotify: spot fy", nothing, "abre o spot fy", 0.6, {"kind": CMD, "has": [["spotify"]]}),
    ("teams: tims", nothing, "abre o tims pra mim", 0.7, {"kind": CMD, "has": [["teams"]]}),
    ("whatsapp: zap", nothing, "abre aí o zap pra mim mano", 0.85, {"kind": CMD, "has": [["whatsapp"]]}),
    ("instagram: insta", nothing, "entra no insta", 0.88, {"kind": CMD, "has": [["instagram"]]}),
    ("mercado livre: meli", nothing, "entra no meli e procura fone bluetooth", 0.8,
     {"kind": CMD, "has": [["mercado livre"], ["fone"]]}),
    ("bloco: blog de notas", nothing, "abre o blog de notas", 0.6, {"kind": CMD, "has": [["bloco de notas", "notepad"]]}),
    ("excel: procurando a palavra", nothing, "abre o, é, como é o nome, aquele de planilha", 0.7,
     {"kind": CMD | {"unclear"}, "has": [["excel", "planilha"]]}),
    # ── giria, muletas, autocorrecao ──────────────────────────────
    ("giria: joga no google", nothing, "joga no google receita de bolo de cenoura", 0.9,
     {"kind": CMD, "has": [["pesquis", "busca", "procur"], ["bolo de cenoura"]]}),
    ("autocorrecao: chrome nao edge", nothing, "abre o chrome, não, o edge", 0.85,
     {"kind": CMD, "has": [["edge"]], "not": ["chrome"]}),
    ("autocorrecao: na verdade", nothing, "abre o word, na verdade abre o google docs", 0.85,
     {"kind": CMD, "has": [["docs"]], "not": ["word"]}),
    ("muletas: tipo, é", nothing, "tipo, é, abre o, o spotify aí", 0.8, {"kind": CMD, "has": [["spotify"]]}),
    ("giria: no talo", nothing, "sobe o volume no talo", 0.85, {"kind": CMD, "has": [["volume"]]}),
    ("giria: printa", nothing, "printa a tela", 0.9, {"kind": CMD, "has": [["print", "captur"]]}),
    ("zap com mensagem", nothing, "manda um zap pra minha mãe falando que vou atrasar", 0.85,
     {"kind": CMD, "has": [["whatsapp"], ["atras"]]}),
    ("pesquisa youtube", nothing, "pesquisa no youtube lofi pra estudar", 0.9,
     {"kind": CMD, "has": [["youtube"], ["lofi"]]}),
    ("pasta: organiza", nothing, "abre a pasta downloads e organiza por tipo", 0.9,
     {"kind": CMD, "has": [["download"], ["organiz"]]}),
    ("site: cria", nothing, "faz um site de cafeteria com html css e js", 0.9,
     {"kind": CMD, "has": [["site"], ["cafeteria"]]}),
    ("ditado: pontuacao", nothing, "abre o bloco de nota e escreve reunião às três vírgula depois almoço", 0.85,
     {"kind": CMD, "has": [["bloco de notas", "notepad"], ["reuni"], ["almo"]], "not": [", . . ?"]}),
    ("excel: preenche", nothing, "abre o excel e preenche a primeira linha com nome idade e cidade", 0.88,
     {"kind": CMD, "has": [["excel"], ["nome"], ["cidade"]]}),
    # ── contexto (algo aberto) ────────────────────────────────────
    ("contexto: toca o segundo", youtube_open, "agora toca o segundo", 0.85,
     {"kind": CMD, "has": [["segund", "2"]], "target": "web"}),
    ("contexto: pausa", youtube_open, "pausa aí", 0.8, {"kind": CMD, "has": [["paus"]], "target": "web"}),
    ("contexto: f5", youtube_open, "dá um f5 aí", 0.8,
     {"kind": CMD, "has": [["recarreg", "atualiz", "f5"]], "target": "web"}),
    ("contexto: celula b2", excel_open, "coloca na célula b2 o valor cem", 0.85,
     {"kind": CMD, "has": [["b2"], ["100", "cem"]], "target": "app:excel"}),
    ("contexto: clica em sistema", settings_open, "clica em sistema", 0.85,
     {"kind": CMD, "has": [["sistema"]], "target": "app:configuracoes"}),
    ("contexto: notepad apaga", notepad_open, "apaga tudo e escreve bom dia", 0.85,
     {"kind": CMD, "has": [["bom dia"]], "target": "app:notepad"}),
    ("contexto: fecha esse", notepad_open, "fecha esse", 0.85, {"kind": CMD, "has": [["fech"]], "target": "app:notepad"}),
    ("contexto: outro app", youtube_open, "abre as configurações do windows", 0.85,
     {"kind": CMD, "has": [["configura"]], "not": ["youtube"], "target": ""}),
    ("contexto: organiza essa", downloads_open, "organiza essa pasta por tipo", 0.85,
     {"kind": CMD, "has": [["organiz"]], "target": "folder"}),
    # ── perguntas e papo ──────────────────────────────────────────
    ("pergunta: horas", nothing, "que horas são", 0.9, {"kind": {"answer"}, "reply": [[":", "hora", "h"]]}),
    ("pergunta: dia", nothing, "que dia é hoje", 0.9, {"kind": {"answer"}}),
    ("pergunta: conta", nothing, "quanto é doze vezes sete", 0.9,
     {"kind": {"answer"} | CMD, "reply_or_cmd": [["84", "oitenta e quatro", "doze", "12"]]}),
    ("pergunta: conhecimento", nothing, "quem pintou a mona lisa", 0.9,
     {"kind": {"answer"}, "reply": [["vinci"]]}),
    ("pergunta: dado ao vivo", nothing, "quanto tá o dólar hoje", 0.9, {"kind": CMD, "has": [["dolar", "dólar"]]}),
    ("papo: valeu", nothing, "valeu mano era isso", 0.9, {"kind": {"chat"}}),
    ("papo: elogio excelente", nothing, "ficou excelente, valeu", 0.9, {"kind": {"chat"}, "not": ["excel"]}),
    ("papo: oi", nothing, "e aí, tudo certo?", 0.9, {"kind": {"chat"}}),
    # ── parar, ruido, conversa de fundo ───────────────────────────
    ("parar: para tudo", nothing, "para tudo", 0.9, {"kind": {"stop"}}),
    ("ruido: hum", nothing, "hum", 0.4, {"kind": {"noise", "unclear"}}),
    ("ruido: fantasma", nothing, "você quer? não tem que dar um pedido de bala", 0.45,
     {"kind": {"noise", "unclear"}}),
    ("fundo: meu time", nothing, "meu time ganhou ontem", 0.85, {"kind": {"noise", "chat"}, "not": ["teams"]}),
    ("fundo: incompleto", nothing, "abre o...", 0.7, {"kind": {"unclear"}}),
    # ── adicionados DEPOIS de ajustar o prompt (checam generalizacao, nao foram usados para ajustar) ──
    ("novo: comentario calor", nothing, "hoje tá um calor absurdo", 0.9, {"kind": {"chat", "noise"}}),
    ("novo: comentario trabalho", nothing, "acabei de chegar do trabalho, tô morto", 0.9, {"kind": {"chat", "noise"}}),
    ("novo: aceita oferta", youtube_offer, "pode", 0.9,
     {"kind": CMD, "has": [["primeir", "1"]], "target": "web"}),
    ("novo: dupla correcao", nothing, "abre o word, não, o excel, não, o powerpoint", 0.85,
     {"kind": CMD, "has": [["powerpoint"]], "not": ["word", "excel"]}),
    ("novo: config misheard", nothing, "abre o note pad e escreve bom dia", 0.8,
     {"kind": CMD, "has": [["bloco de notas", "notepad"], ["bom dia"]]}),
]


def _norm(s: str) -> str:
    from core.lexicon import norm
    return norm(s)


def _groups_ok(text: str, groups) -> list:
    t = _norm(text)
    return [g for g in groups if not any(_norm(w) in t for w in g)]


def run_case(case, trial):
    from core.session import Session
    from core.voice.understand import understand
    name, setup, heard, conf, exp = case
    s = Session()
    setup(s)
    ctx = "" if s.empty else s.context_block(1400)
    t0 = time.time()
    u = understand(heard, conf, ctx, list(RECENT), session=s) if _accepts_session() else \
        understand(heard, conf, ctx, list(RECENT))
    secs = time.time() - t0
    kind = u.get("kind", "")
    cmd = u.get("command") or u.get("guess") or ""
    reply = u.get("reply") or ""
    fails = []
    if kind not in exp["kind"]:
        fails.append(f"kind={kind} (esperado {'/'.join(sorted(exp['kind']))})")
    if exp.get("has") and kind in ("command", "unclear"):
        for g in _groups_ok(cmd, exp["has"]):
            fails.append(f"pedido sem {'/'.join(g)}")
    for w in exp.get("not", []):
        if _norm(w) in _norm(cmd):
            fails.append(f"pedido contém '{w}'")
    if exp.get("reply") and kind == "answer":
        for g in _groups_ok(reply, exp["reply"]):
            fails.append(f"resposta sem {'/'.join(g)}")
    if exp.get("reply_or_cmd"):
        for g in _groups_ok(reply + " " + cmd, exp["reply_or_cmd"]):
            fails.append(f"sem {'/'.join(g)}")
    tgt = None
    if "target" in exp and "target" in u:
        tgt = u.get("target") or ""
        if tgt != exp["target"]:
            fails.append(f"alvo={tgt or '-'} (esperado {exp['target'] or 'nenhum'})")
    # qualidade da fala
    style = []
    if reply:
        words = len(reply.split())
        limit = 45 if kind == "answer" else 16
        if words > limit:
            style.append(f"fala longa ({words} palavras)")
        if ROBOTIC.search(reply):
            style.append("bordão robótico")
        if reply in RECENT:
            style.append("repetiu fala recente")
    elif kind in ("command", "chat", "answer", "unclear", "stop"):
        style.append("sem fala")
    return {"name": name, "heard": heard, "trial": trial, "kind": kind, "command": cmd, "reply": reply,
            "target": tgt, "via": u.get("via", ""), "seconds": round(secs, 2), "fails": fails, "style": style,
            "pass": not fails}


def _accepts_session() -> bool:
    import inspect
    from core.voice.understand import understand
    return "session" in inspect.signature(understand).parameters


def main(argv):
    from core.ai_client import get_client
    trials = 2
    if "--trials" in argv:
        trials = int(argv[argv.index("--trials") + 1])
    flt = [a for a in argv if not a.startswith("--") and not a.isdigit()]
    chosen = [c for c in CASES if not flt or any(f.lower() in c[0].lower() for f in flt)]
    c0 = get_client().metrics["total_cost_usd"]
    results = []
    for case in chosen:
        for t in range(trials):
            r = run_case(case, t)
            results.append(r)
            mark = "OK  " if r["pass"] else "FAIL"
            print(f"{mark} | {r['name']:30} | {r['kind']:8} {r['via']:7} {r['seconds']:4.1f}s | "
                  f"{r['command'][:55]:55} | {r['reply'][:50]}")
            for f in r["fails"] + r["style"]:
                print(f"       ✗ {f}")
    cost = get_client().metrics["total_cost_usd"] - c0
    summary = summarize(results, chosen, trials, cost)
    print("\n" + "\n".join(summary))
    if "--vault" in argv:
        write_report(results, summary)
    return 0


def summarize(results, chosen, trials, cost):
    import statistics
    n = len(results)
    ok = sum(r["pass"] for r in results)
    per_case = {}
    for r in results:
        per_case.setdefault(r["name"], []).append(r["pass"])
    stable = sum(all(v) for v in per_case.values())
    flaky = [k for k, v in per_case.items() if any(v) and not all(v)]
    style_bad = sum(bool(r["style"]) for r in results)
    lat = [r["seconds"] for r in results]
    fast = sum(r["via"] in ("rapido", "local") for r in results)
    replies = [r["reply"] for r in results if r["reply"]]
    variety = len(set(replies)) / max(1, len(replies))
    return [f"Acerto: {ok}/{n} ({ok / max(1, n):.0%}) · casos sempre certos: {stable}/{len(per_case)} · "
            f"instáveis: {len(flaky)} {flaky[:6]}",
            f"Fala: {n - style_bad}/{n} sem problema de estilo · variedade {variety:.0%}",
            f"Tempo: mediana {statistics.median(lat):.2f}s · p90 {sorted(lat)[int(0.9 * (n - 1))]:.2f}s · "
            f"sem modelo {fast}/{n}",
            f"Custo: US$ {cost:.3f} ({trials} rodada(s) × {len(chosen)} casos)"]


def write_report(results, summary):
    from datetime import date
    from core.brain import get_brain
    lines = ["---", "tipo: avaliacao", "tags: [avaliacao, voz]", "cssclasses: [agent-maestro]", "---",
             "# 🎙️ Avaliação de voz", "", "← [[Modo voz]] · [[Dicionario de voz]] · [[Persona do assistente]]", "",
             f"> [!info] Última rodada: {date.today().isoformat()}"] + [f"> {s}" for s in summary] + [
             "> Gerado por `scripts/eval_voice.py --vault` (só entendimento; nada é executado).", "",
             "| | Caso | Ouvido | Entendeu | Pedido limpo | Fala | Problema |", "|---|---|---|---|---|---|---|"]
    for r in results:
        if r["trial"]:
            continue
        cell = lambda s: str(s).replace("|", "/")[:70]
        lines.append(f"| {'✅' if r['pass'] else '❌'} | {r['name']} | {cell(r['heard'])} | {r['kind']} | "
                     f"{cell(r['command']) or '-'} | {cell(r['reply']) or '-'} | "
                     f"{cell('; '.join(r['fails'] + r['style'])) or '-'} |")
    path = get_brain().root / "00 Maestro" / "Avaliacao de voz.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"relatório: {path}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
