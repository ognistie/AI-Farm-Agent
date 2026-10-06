"""
Benchmark de custo: AI Farm Agent x Claude Cowork x ChatGPT Work, nas MESMAS tarefas.

Lado AI Farm (MEDIDO): cada tarefa roda DE VERDADE no PC pelo caminho da voz
(entendimento -> conversa -> Maestro -> agentes -> pilotos -> resposta). Cada chamada ao
modelo e registrada (tokens de entrada/saida/cache, custo pela tabela da Anthropic), assim
como cada acao executada e o tamanho de cada leitura de tela por texto.

Lado concorrentes (ESTIMADO): Cowork e ChatGPT Work nao publicam custo por tarefa.
Estimamos o custo de API equivalente de um agente de tela (captura de tela a cada passo,
historico na conversa, prompt de sistema grande cacheado) usando:
  - o NUMERO DE PASSOS que a nossa execucao precisou (eles nao gastam menos passos que isso:
    premissa favoravel a eles);
  - o preco de API publico do modelo de cada um;
  - dois cenarios: "enxuto" (favoravel a eles) e "tipico".
Todas as premissas ficam em PREMISSAS e no relatorio.

Rodar (abre e usa apps no PC! nada destrutivo, nada enviado):
    python scripts/bench_cost.py --run --reps 2
    python scripts/bench_cost.py --analyze reports/bench_cost_XXXX.json   # recalcula sem rodar
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
from datetime import datetime
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

BENCH_DIR = Path.home() / "Documents" / "bench_ai_farm_tmp"

# (id, conversa, categoria, fala). Mesma "conversa" = continua no que ficou aberto.
TASKS = [
    ("d01", "notas", "DESKTOP", "abre o bloco de notas e escreve: lista de compras: arroz, feijão e café"),
    ("d02", "notas", "DESKTOP", "agora escreve embaixo: comprar pão também"),
    ("d03", None, "DESKTOP", "abre a calculadora e calcula 128 vezes 47"),
    ("d04", None, "DESKTOP", "abre as configurações do windows"),
    ("d05", None, "DESKTOP", "abre a página de bluetooth nas configurações"),
    ("d06", "config", "DESKTOP", "abre as configurações do windows"),
    ("d07", "config", "DESKTOP", "clica em sistema"),
    ("d08", None, "DESKTOP", "abre o excel e preenche a primeira linha com Produto, Preço e Quantidade"),
    ("d09", None, "DESKTOP", "abre o paint"),
    ("d10", None, "DESKTOP", "abre o bloco de notas e escreve um poema curto sobre café"),
    ("d11", None, "DESKTOP", "abre a tela de bloqueio nas configurações"),
    ("w01", None, "WEB", "pesquisa no google previsão do tempo em São Paulo"),
    ("w02", "yt", "WEB", "abre o youtube e pesquisa lofi para estudar"),
    ("w03", "yt", "WEB", "abre o segundo vídeo"),
    ("w04", None, "WEB", "entra na wikipédia e me diz em que ano foi fundada a cidade de Curitiba"),
    ("w05", None, "WEB", "pesquisa o preço do fone JBL Tune 520 no mercado livre e me fala o mais barato"),
    ("w06", None, "WEB", "abre o g1"),
    ("w07", None, "WEB", "pesquisa no youtube receita de pão de queijo"),
    ("w08", None, "WEB", "abre o github"),
    ("w09", None, "WEB", "quanto tá o dólar hoje?"),
    ("w10", None, "WEB", "abre o site da receita federal"),
    ("c01", "site", "CODE", "cria um site simples para a padaria Pão Dourado com html e css"),
    ("c02", "site", "CODE", "muda a cor do título para roxo"),
    ("c03", None, "CODE", "cria um script python que conta quantas palavras tem num texto"),
    ("f01", None, "FILE", f"organiza a pasta {BENCH_DIR} por tipo de arquivo"),
    ("t01", None, "DATA", "faz uma planilha de gastos mensais com 5 categorias e o total"),
    ("q01", None, "CHAT", "que horas são"),
    ("q02", None, "CHAT", "quanto é 15% de 320"),
    ("q03", None, "CHAT", "quem escreveu Dom Casmurro"),
    ("q04", None, "CHAT", "valeu, ficou ótimo"),
]

# ── premissas dos concorrentes (todas publicas ou explicitamente assumidas) ──
SCREEN = (1920, 1200)
PREMISSAS = {
    "usd_brl": 4.97, "spread_cartao": 0.04, "iof": 0.035,       # dolar 06/10/2026, cartao, IOF
    "precos": {  # US$ por 1M tokens (entrada, saida, leitura de cache)
        "claude-sonnet-5 (nosso)": (2.00, 10.00, 0.20),
        "claude-opus-5-5 (Cowork tipico)": (4.00, 20.00, 0.20),
        "claude-sonnet-5-5 (Cowork enxuto)": (2.00, 10.00, 0.20),
        "gpt-6-sol (ChatGPT Work)": (2.00, 10.00, 0.20),
    },
    # tokens de uma captura 1920x1200: Claude ~ largura*altura/750 apos reduzir para ~1,15 MP;
    # OpenAI "high detail": reduz para 1229x768 -> 6 blocos de 512px x 170 + 85
    "tokens_captura": {"claude": 1533, "openai": 1105},
    "cenarios": {
        "enxuto": {"sistema": 4000, "capturas_no_historico": 1, "saida_por_passo": 150, "texto_por_passo": 120},
        "tipico": {"sistema": 8000, "capturas_no_historico": 3, "saida_por_passo": 400, "texto_por_passo": 200},
    },
    "assinaturas_brl": {"ChatGPT Plus": 99.90, "ChatGPT Go (sem Work)": 39.99,
                        "Claude Pro (US$ 20)": 20.0, "Claude Max 5x (US$ 100)": 100.0},
}
WAIT_ACTIONS = {"wait", "focus_window"}
PILOT_AGENTS = {"APP_PILOT", "WEB_PILOT"}


def brl(usd: float) -> float:
    p = PREMISSAS
    return usd * p["usd_brl"] * (1 + p["spread_cartao"]) * (1 + p["iof"])


# ═════════════════════════════════════════════════════════════════════
# Execucao (medida)
# ═════════════════════════════════════════════════════════════════════
class Recorder:
    def __init__(self):
        self.calls, self.actions, self.snaps = [], [], []
        self.lock = threading.Lock()

    def reset(self):
        with self.lock:
            self.calls, self.actions, self.snaps = [], [], []


def _png_size(b64: str):
    import base64
    import struct
    try:
        raw = base64.b64decode(b64[:200] + "=" * (-len(b64[:200]) % 4))
        if raw[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", raw[16:24])
    except Exception:
        pass
    return None


def instrument(rec: Recorder):
    import core.ai_client as aic
    import core.automation as auto
    import core.browser_uia as B

    orig_msg = aic.AIClient.message_with_meta

    def message_with_meta(self, model, system, user_content, max_tokens=8000, images=None, effort=None, agent=""):
        meta = orig_msg(self, model=model, system=system, user_content=user_content, max_tokens=max_tokens,
                        images=images, effort=effort, agent=agent)
        with rec.lock:
            rec.calls.append({"agent": agent or "?", "model": model, "in": meta["input_tokens"],
                              "out": meta["output_tokens"], "cache_r": meta["cache_read_tokens"],
                              "cache_w": meta["cache_write_tokens"], "cost": meta["cost_usd"],
                              "images": [_png_size(i.get("base64", "")) for i in (images or [])],
                              "ms": meta["duration_ms"]})
        return meta
    aic.AIClient.message_with_meta = message_with_meta

    orig_exec = auto.AutomationEngine.execute

    def execute(self, action, params, dry_run=False):
        r = orig_exec(self, action, params, dry_run)
        with rec.lock:
            rec.actions.append({"action": action, "ok": bool(r.get("success")) if isinstance(r, dict) else None})
        return r
    auto.AutomationEngine.execute = execute

    orig_render = B.Snapshot.render

    def render(self, *a, **k):
        out = orig_render(self, *a, **k)
        with rec.lock:
            rec.snaps.append(len(out))
        return out
    B.Snapshot.render = render


def prepare_files():
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    for name, body in [("relatorio.txt", "texto"), ("notas.md", "# notas"), ("dados.csv", "a,b\n1,2"),
                       ("foto.png", ""), ("contrato.pdf", "%PDF-1.4"), ("planilha.xlsx", ""),
                       ("musica.mp3", ""), ("script.py", "print(1)")]:
        (BENCH_DIR / name).write_text(body, encoding="utf-8")


def run(reps: int, out_path: Path):
    from desktop.event_bus import bus
    from desktop.controller import Controller
    from desktop.voice import VoiceController

    rec = Recorder()
    instrument(rec)
    ctrl = Controller()
    ev = {"done": threading.Event(), "reply": threading.Event(), "entry": None, "reply_text": ""}

    def on_cmd(p):
        ctrl.execute_task(p["text"], dry_run=False, generate_report=False)

    def on_done(p):
        ev["entry"] = (p or {}).get("entry")
        ev["done"].set()

    def on_reply(p):
        ev["reply_text"] = (p or {}).get("text", "")
        ev["reply"].set()
    bus.on("voice_command", on_cmd)
    bus.on("history_changed", on_done)
    bus.on("assistant_message", on_reply)

    class Mute:
        speaking = False
        def speak(self, t): pass
        def stop(self): pass
        def wait(self, timeout=0): pass

    vc = VoiceController(ctrl, {"progress_after_s": 0})
    vc.tts = Mute()
    results = {"started": datetime.now().isoformat(timespec="seconds"), "reps": reps, "premissas": PREMISSAS,
               "runs": []}
    for rep in range(reps):
        prepare_files()
        last_group = "__"
        for tid, group, cat, text in TASKS:
            if group is None or group != last_group:
                ctrl.new_session()
                time.sleep(0.3)
            last_group = group
            rec.reset()
            ev["done"].clear(); ev["reply"].clear(); ev["entry"] = None; ev["reply_text"] = ""
            t0 = time.time()
            u = vc.handle_text(text, 0.92, mode="record")
            kind = u.get("kind", "")
            executed = False
            if kind == "command":
                executed = ev["done"].wait(360)
                ev["reply"].wait(25)
            entry = ev["entry"] or {}
            ok = (kind in ("chat", "answer") and cat == "CHAT") or bool(executed and entry.get("success"))
            with rec.lock:
                row = {"rep": rep, "id": tid, "cat": cat, "text": text, "kind": kind, "via": u.get("via", ""),
                       "ok": ok, "timeout": kind == "command" and not executed,
                       "seconds": round(time.time() - t0, 1), "calls": list(rec.calls),
                       "actions": list(rec.actions), "snaps": list(rec.snaps),
                       "reply": (ev["reply_text"] or u.get("reply", ""))[:200]}
            results["runs"].append(row)
            cost = sum(c["cost"] for c in row["calls"])
            print(f"[{rep}] {tid} {cat:7} {'OK  ' if ok else 'FAIL'} {row['seconds']:6.1f}s  US$ {cost:.4f}  "
                  f"calls={len(row['calls'])} acoes={len(row['actions'])}  {text[:50]}", flush=True)
            out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
            if kind == "command" and not executed:
                ctrl.force_stop()
                time.sleep(3)
            time.sleep(1.5)
    shutil.rmtree(BENCH_DIR, ignore_errors=True)
    results["finished"] = datetime.now().isoformat(timespec="seconds")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    return results


# ═════════════════════════════════════════════════════════════════════
# Analise
# ═════════════════════════════════════════════════════════════════════
def steps_of(row) -> dict:
    """Passos de interface que um agente de tela precisaria (no minimo) para a mesma tarefa."""
    acts = [a["action"] for a in row["actions"]]
    pilot_turns = sum(1 for c in row["calls"] if c["agent"] in PILOT_AGENTS)
    routine = [a for a in acts if a not in WAIT_ACTIONS and a not in ("app_task", "browser_task")]
    llm_free = [a for a in routine]          # passos de rotina: no nosso caso, sem modelo
    return {"gui": len(routine) + pilot_turns, "routine": len(llm_free), "pilot": pilot_turns}


def competitor_cost(row, who: str, scen: str) -> float:
    """Custo de API estimado (US$) de um agente de tela fazendo a mesma tarefa."""
    p = PREMISSAS
    sc = p["cenarios"][scen]
    if who == "cowork":
        pin, pout, pcache = p["precos"]["claude-opus-5-5 (Cowork tipico)" if scen == "tipico"
                                       else "claude-sonnet-5-5 (Cowork enxuto)"]
        img = p["tokens_captura"]["claude"]
    else:
        pin, pout, pcache = p["precos"]["gpt-6-sol (ChatGPT Work)"]
        img = p["tokens_captura"]["openai"]
    S, k, out_t, txt = sc["sistema"], sc["capturas_no_historico"], sc["saida_por_passo"], sc["texto_por_passo"]
    our_out = sum(c["out"] for c in row["calls"])
    cat = row["cat"]
    if cat == "CHAT":
        turns, shots = 1, False
    elif cat in ("CODE", "DATA", "FILE"):
        turns, shots = max(3, steps_of(row)["gui"] + 2), False    # ferramentas de arquivo, sem captura
    else:
        turns, shots = max(2, steps_of(row)["gui"] + 1), True      # +1: conferir o resultado na tela
    cost = 0.0     # prompt de sistema do produto ja esta no cache deles (favoravel a eles: so leitura)
    hist = []
    for _ in range(turns):
        fresh = txt + (img if shots else 0)
        cached = S + sum(hist[-k:]) if shots else S + sum(hist)
        cost += fresh * pin + cached * pcache + out_t * pout
        hist.append(fresh)
    # conteudo gerado (site, script, planilha, poema): eles escrevem no minimo o mesmo tanto que nos
    content_out = max(0, our_out - turns * out_t) if cat in ("CODE", "DATA") or row["id"] == "d10" else 0
    cost += content_out * pout
    return cost / 1_000_000


def analyze(data: dict) -> dict:
    import statistics as st
    runs = data["runs"]
    ids = list(dict.fromkeys(r["id"] for r in runs))
    per_task = []
    for tid in ids:
        rs = [r for r in runs if r["id"] == tid]
        ours = [sum(c["cost"] for c in r["calls"]) for r in rs]
        row0 = rs[0]
        comp = {f"{w}_{s}": st.mean(competitor_cost(r, w, s) for r in rs)
                for w in ("cowork", "chatgpt") for s in ("enxuto", "tipico")}
        per_task.append({"id": tid, "cat": row0["cat"], "text": row0["text"], "ok": sum(r["ok"] for r in rs),
                         "n": len(rs), "ours": st.mean(ours), "ours_min": min(ours), "ours_max": max(ours),
                         "calls": st.mean(len(r["calls"]) for r in rs),
                         "steps": st.mean(steps_of(r)["gui"] for r in rs),
                         "routine": st.mean(steps_of(r)["routine"] for r in rs),
                         "seconds": st.mean(r["seconds"] for r in rs), **comp})
    tot = {k: sum(t[k] for t in per_task) for k in ("ours", "cowork_enxuto", "cowork_tipico",
                                                      "chatgpt_enxuto", "chatgpt_tipico")}
    # metodos de economia (medidos)
    calls = [c for r in runs for c in r["calls"]]
    cache_r = sum(c["cache_r"] for c in calls)
    in_t = sum(c["in"] for c in calls)
    out_t = sum(c["out"] for c in calls)
    snaps = [s for r in runs for s in r["snaps"]]
    snap_tokens = st.mean(snaps) / 3.2 if snaps else 0
    routine_steps = sum(steps_of(r)["routine"] for r in runs)
    pilot_calls = [c for c in calls if c["agent"] in PILOT_AGENTS]
    pilot_avg = st.mean(c["cost"] for c in pilot_calls) if pilot_calls else 0.0
    via = [r["via"] for r in runs]
    images = sum(1 for c in calls for i in c["images"])
    sonnet_cost = sum(c["cost"] for c in calls)
    opus_cost = sum((c["in"] * 4 + c["cache_r"] * 0.2 + c["cache_w"] * 5 + c["out"] * 20) / 1e6 for c in calls)
    savings = {
        "cache_lido_tokens": cache_r, "entrada_tokens": in_t, "saida_tokens": out_t,
        "cache_economia_usd": cache_r * (2.00 - 0.20) / 1e6,
        "leitura_texto_tokens_media": round(snap_tokens), "captura_tokens": PREMISSAS["tokens_captura"]["claude"],
        "leituras_de_tela": len(snaps), "capturas_enviadas": images,
        "passos_de_rotina_sem_modelo": routine_steps, "custo_medio_passo_piloto": pilot_avg,
        "rotinas_economia_usd": routine_steps * pilot_avg,
        "falas_sem_modelo": sum(v in ("rapido", "local") for v in via), "falas": len(via),
        "sonnet_vs_opus": (sonnet_cost, opus_cost),
    }
    by_agent: dict = {}
    for c in calls:
        b = by_agent.setdefault(c["agent"], [0, 0.0])
        b[0] += 1
        b[1] += c["cost"]
    savings["por_agente"] = sorted(((k, v[0], v[1]) for k, v in by_agent.items()), key=lambda x: -x[2])
    n_runs = len(runs)
    return {"per_task": per_task, "total": tot, "savings": savings, "n_runs": n_runs,
            "success": (sum(r["ok"] for r in runs), n_runs), "reps": data.get("reps", 1),
            "started": data.get("started"), "finished": data.get("finished")}


def report(a: dict) -> str:
    T = a["total"]
    per = a["per_task"]
    n_tasks = len(per)
    ok, n = a["success"]
    s = a["savings"]
    ratio = lambda x: x / T["ours"] if T["ours"] else 0
    fmt = lambda u: f"US$ {u:.4f} (R$ {brl(u):.3f})"
    L = ["---", "tipo: benchmark", "tags: [benchmark, custo]", "cssclasses: [agent-maestro]", "---",
         "# 💰 Benchmark de custo — AI Farm x Claude Cowork x ChatGPT Work", "",
         "← [[Maestro]] · [[Avaliacao de voz]] · [[Avaliacao de conversas]]", "",
         f"> [!info] Rodada {a['started']} → {a['finished']} · {n_tasks} tarefas × {a['reps']} repetições · "
         f"sucesso {ok}/{n}",
         "> **AI Farm = medido** (cada chamada ao modelo, tokens e custo reais). **Cowork e ChatGPT Work = estimados**: "
         "custo de API de um agente de tela com o MESMO número de passos que nós precisamos (premissa favorável a eles), "
         "nos cenários *enxuto* (favorável a eles) e *típico*. Gerado por `scripts/bench_cost.py`.", "",
         "## Resultado (soma das tarefas, média por repetição)", "",
         "| Sistema | Custo das tarefas | Quantas vezes o AI Farm é mais barato |", "|---|---|---|",
         f"| **AI Farm (medido)** | **{fmt(T['ours'])}** | — |",
         f"| Claude Cowork — enxuto (Sonnet 5.5) | {fmt(T['cowork_enxuto'])} | **{ratio(T['cowork_enxuto']):.1f}×** |",
         f"| Claude Cowork — típico (Opus 5.5) | {fmt(T['cowork_tipico'])} | **{ratio(T['cowork_tipico']):.1f}×** |",
         f"| ChatGPT Work — enxuto (GPT-6 Sol) | {fmt(T['chatgpt_enxuto'])} | **{ratio(T['chatgpt_enxuto']):.1f}×** |",
         f"| ChatGPT Work — típico (GPT-6 Sol) | {fmt(T['chatgpt_tipico'])} | **{ratio(T['chatgpt_tipico']):.1f}×** |", "",
         "## Por categoria", "", "| Categoria | Tarefas | AI Farm | Cowork (enxuto–típico) | ChatGPT Work (enxuto–típico) |",
         "|---|---|---|---|---|"]
    for cat in ("DESKTOP", "WEB", "CODE", "FILE", "DATA", "CHAT"):
        g = [t for t in per if t["cat"] == cat]
        if not g:
            continue
        o = sum(t["ours"] for t in g)
        rng = lambda a_, b_: f"{ratio_cat(a_, o)}–{ratio_cat(b_, o)}"
        L.append(f"| {cat} | {len(g)} | US$ {o:.4f} | US$ {sum(t['cowork_enxuto'] for t in g):.4f}–"
                 f"{sum(t['cowork_tipico'] for t in g):.4f} ({rng(sum(t['cowork_enxuto'] for t in g), sum(t['cowork_tipico'] for t in g))}) | "
                 f"US$ {sum(t['chatgpt_enxuto'] for t in g):.4f}–{sum(t['chatgpt_tipico'] for t in g):.4f} "
                 f"({rng(sum(t['chatgpt_enxuto'] for t in g), sum(t['chatgpt_tipico'] for t in g))}) |")
    L += ["", "## Por tarefa", "", "| | Tarefa | Sucesso | Passos | Chamadas | AI Farm (mín–máx) | Cowork típ. | ChatGPT típ. |",
          "|---|---|---|---|---|---|---|---|"]
    for t in per:
        L.append(f"| {t['id']} | {t['text'][:60]} | {t['ok']}/{t['n']} | {t['steps']:.0f} | {t['calls']:.0f} | "
                 f"US$ {t['ours']:.4f} ({t['ours_min']:.4f}–{t['ours_max']:.4f}) | US$ {t['cowork_tipico']:.4f} | "
                 f"US$ {t['chatgpt_tipico']:.4f} |")
    so, op = s["sonnet_vs_opus"]
    L += ["", f"## De onde vem a economia (medido nas {a['n_runs']} execuções)", "",
          f"- **Leitura da tela por texto (acessibilidade) em vez de captura:** {s['leituras_de_tela']} leituras, "
          f"~{s['leitura_texto_tokens_media']} tokens cada, contra ~{s['captura_tokens']} de uma captura 1920×1200 "
          f"(e a captura entra de novo no histórico a cada passo). Capturas enviadas ao modelo: {s['capturas_enviadas']}.",
          f"- **Rotinas sem modelo:** {s['passos_de_rotina_sem_modelo']} passos executados sem chamar a IA "
          f"(um agente de tela pagaria cada um; a ~US$ {s['custo_medio_passo_piloto']:.4f} por passo do nosso piloto = "
          f"~US$ {s['rotinas_economia_usd']:.3f} poupados).",
          f"- **Respostas na hora sem modelo (voz):** {s['falas_sem_modelo']}/{s['falas']} falas entendidas por "
          "atalho/resposta local.",
          f"- **Cache de prompt:** {s['cache_lido_tokens']:,} tokens lidos do cache (de {s['entrada_tokens'] + s['cache_lido_tokens']:,} "
          f"de entrada) = US$ {s['cache_economia_usd']:.3f} poupados.",
          f"- **Modelo e esforço:** Sonnet 5 com esforço baixo/médio. Os mesmos tokens no Opus 5.5 custariam "
          f"US$ {op:.3f} em vez de US$ {so:.3f} ({op / so if so else 0:.1f}×).",
          "- **Contexto enxuto:** cada chamada leva só o necessário (sem reenviar a conversa inteira nem capturas antigas).",
          "", "### Quanto o AI Farm custaria sem cada método (por repetição das 30 tarefas)", "",
          "| Configuração | Custo | vs. atual |", "|---|---|---|",
          f"| Atual (medido) | US$ {T['ours']:.3f} | 1,0× |"] + _ablation(a) + [
          "", "### Para onde vai o custo do AI Farm", "",
          "| Etapa | Chamadas | Custo | Parte |", "|---|---|---|---|"] + [
          f"| {ag} | {n} | US$ {c:.3f} | {c / sum(x[2] for x in s['por_agente']):.0%} |" for ag, n, c in s["por_agente"]] + [
          "", "> [!tip] Próxima economia", "> Maestro + entendimento de voz + resposta final são uma camada fixa em todo pedido. "
          "Rotear direto os pedidos simples (abrir, pesquisar) e responder com frase pronta quando não há dado a contar cortaria boa parte dela.",
          "", "## Quanto o usuário paga por mês", "",
          "Os dois concorrentes cobram **assinatura** com limite de uso (janelas de 5 h); nenhum publica custo por tarefa. "
          "Com o custo médio medido por tarefa do AI Farm:", "",
          "| Pedidos/mês | AI Farm (R$) | ChatGPT Plus | Claude Pro (Cowork) |", "|---|---|---|---|"]
    per_task_brl = brl(T["ours"] / n_tasks) if n_tasks else 0
    pro_brl = brl(20.0)
    for vol in (150, 300, 600, 900, 1500):
        L.append(f"| {vol} | R$ {per_task_brl * vol:.2f} | R$ 99,90 ({99.90 / (per_task_brl * vol):.1f}×) | "
                 f"R$ {pro_brl:.2f} ({pro_brl / (per_task_brl * vol):.1f}×) |")
    L += ["", f"Custo médio por tarefa medido: **R$ {per_task_brl:.3f}** · empate com o Plus: "
          f"**{99.90 / per_task_brl:.0f} pedidos/mês** · com o Claude Pro: **{pro_brl / per_task_brl:.0f} pedidos/mês**.", "",
          "## Premissas", "",
          f"- Câmbio: US$ 1 = R$ {PREMISSAS['usd_brl']} + {PREMISSAS['spread_cartao']:.0%} spread do cartão + "
          f"{PREMISSAS['iof']:.1%} IOF.",
          "- Preços de API (US$/1M entrada · saída · cache): " + "; ".join(
              f"{k}: {v[0]} · {v[1]} · {v[2]}" for k, v in PREMISSAS["precos"].items()) + ".",
          f"- Captura de tela {SCREEN[0]}×{SCREEN[1]}: Claude ~{PREMISSAS['tokens_captura']['claude']} tokens, "
          f"OpenAI ~{PREMISSAS['tokens_captura']['openai']} tokens (fórmula pública de visão; GPT-6 pode diferir).",
          "- Cenários do agente de tela: " + "; ".join(
              f"**{k}**: sistema {v['sistema']} tokens (cacheado), {v['capturas_no_historico']} captura(s) no histórico, "
              f"{v['saida_por_passo']} tokens de saída por passo" for k, v in PREMISSAS["cenarios"].items()) + ".",
          "- Passos dos concorrentes = passos que NÓS precisamos + 1 para conferir (um agente de tela costuma precisar de mais). "
          "Código/planilha/arquivos: ferramentas de arquivo, sem captura, e no mínimo o mesmo texto gerado.",
          "- Não medido: qualidade comparada e limites reais das assinaturas (dependem de rodar as mesmas tarefas nas contas do usuário).",
          "", "## Fontes", "- Preços ChatGPT (BR): https://chatgpt.com/pt-BR/pricing/",
          "- GPT-6 Sol API: https://www.eesel.ai/blog/gpt-6-sol-pricing",
          "- Claude Cowork nos planos: https://fast.io/resources/claude-cowork-pricing-plans/",
          "- Limites ChatGPT Work: https://www.ai-toolbox.co/chatgpt-management-and-productivity/chatgpt-limits-messages-tokens-rate-2026",
          "- Preços da API Claude: tabela oficial de modelos da Anthropic (Sonnet 5 $2/$10; Opus 5.5 $4/$20; Sonnet 5.5 $2/$10)."]
    return "\n".join(L) + "\n"


def _ablation(a: dict) -> list:
    """Sem cache / sem rotinas / com Opus: quanto a mesma rodada custaria (por repeticao)."""
    T, s, reps = a["total"], a["savings"], max(1, a["reps"])
    base = T["ours"]
    no_cache = base + s["cache_economia_usd"] / reps
    no_routines = base + s["rotinas_economia_usd"] / reps
    so, op = s["sonnet_vs_opus"]
    k = op / so if so else 1
    rows = [("Sem cache de prompt", no_cache), ("Sem rotinas (todo passo pela IA)", no_routines),
            ("Com Opus 5.5 em vez de Sonnet 5", base * k),
            ("Sem cache, sem rotinas e com Opus", (no_cache + no_routines - base) * k)]
    return [f"| {n} | US$ {v:.3f} | {v / base:.1f}× |" for n, v in rows]


def ratio_cat(theirs: float, ours: float) -> str:
    return f"{theirs / ours:.1f}×" if ours else "—"


def main(argv):
    if "--analyze" in argv:
        path = Path(argv[argv.index("--analyze") + 1])
        data = json.loads(path.read_text(encoding="utf-8"))
    elif "--run" in argv:
        reps = int(argv[argv.index("--reps") + 1]) if "--reps" in argv else 2
        if "--only" in argv:                      # teste rapido: so alguns ids
            keep = set(argv[argv.index("--only") + 1].split(","))
            TASKS[:] = [t for t in TASKS if t[0] in keep]
        out = ROOT / "reports" / f"bench_cost_{datetime.now():%Y%m%d_%H%M%S}.json"
        out.parent.mkdir(exist_ok=True)
        data = run(reps, out)
        print(f"dados: {out}")
    else:
        print(__doc__)
        return 1
    a = analyze(data)
    md = report(a)
    from core.brain import get_brain
    note = get_brain().root / "00 Maestro" / "Benchmark de custo.md"
    note.write_text(md, encoding="utf-8")
    print(md)
    print(f"relatório: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
