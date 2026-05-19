"""
Suite criativa — 18 tarefas em dominios e padroes que as suites anteriores
nao cobriram:

  - Jogos CLI e web (jogo da velha, jogo da forca, pedra-papel-tesoura)
  - Conversores (markdown->html, moedas, temperatura)
  - Sistemas de negocio reais (pizzaria, academia, cinema, banco)
  - Utilities especificas (validador email, parser cron, lorem ipsum)
  - Networking simples (HTTP server vanilla)
  - Sites infantis/educacionais

Objetivo: descobrir onde o CodeAgent ainda erra com prompts FORA do padrao
"site sobre X" / "sistema profissional em python". Cada falha vira input
para o proximo ciclo de fix.

Cost estimate: 18 tasks × ~$0.012 (mix Sonnet/Haiku) ≈ $0.20 total

Uso:
    cd ai-farm-agent
    python scripts/run_creative_suite.py [--quick] [--filter <termo>]

  --quick: roda apenas as 6 primeiras (smoke check)
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INNER_DIR = SCRIPT_DIR.parent
OUTER_DIR = INNER_DIR.parent

try:
    from dotenv import load_dotenv
    for env_path in (INNER_DIR / ".env", OUTER_DIR / ".env"):
        if env_path.exists():
            load_dotenv(str(env_path), override=True)
            print(f"[suite] .env carregado de {env_path}")
            break
except ImportError:
    print("[suite] WARN: python-dotenv nao instalado")

sys.path.insert(0, str(INNER_DIR))

from agents.code_agent import CodeAgent


TASKS = [
    # ─── L1: utilities curtas, dominios novos ────────────────────────
    {
        "id": 1,
        "category": "utility",
        "complexity": "L1",
        "domain": "validation",
        "prompt": "Crie um arquivo python que valida endereco de email com regex.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["import re", "from re"],
        },
    },
    {
        "id": 2,
        "category": "utility",
        "complexity": "L1",
        "domain": "math",
        "prompt": "Crie um arquivo python que gera os primeiros N numeros primos com argparse.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["argparse", "ArgumentParser"],
        },
    },
    {
        "id": 3,
        "category": "utility",
        "complexity": "L1",
        "domain": "dev-tools",
        "prompt": "Crie um arquivo python que gera Lorem Ipsum aleatorio (N paragrafos).",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    {
        "id": 4,
        "category": "utility",
        "complexity": "L1",
        "domain": "dev-tools",
        "prompt": "Crie um arquivo python que faz parse de expressao cron e descreve em linguagem natural.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    {
        "id": 5,
        "category": "utility",
        "complexity": "L1",
        "domain": "converter",
        "prompt": "Crie um conversor de temperatura (Celsius, Fahrenheit, Kelvin) em HTML, CSS e JavaScript inline (1 arquivo).",
        "expect": {
            "min_html": 1,
            "max_files": 1,
            "must_contain_any": ["<script", "celsius", "fahrenheit"],
        },
    },
    {
        "id": 6,
        "category": "utility",
        "complexity": "L1",
        "domain": "converter",
        "prompt": "Crie um arquivo python que converte Markdown para HTML usando a biblioteca markdown.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["import markdown", "from markdown"],
        },
    },

    # ─── L2: jogos CLI Python ────────────────────────────────────────
    {
        "id": 7,
        "category": "game-cli",
        "complexity": "L2",
        "domain": "games",
        "prompt": "Crie um jogo da velha em Python no terminal, dois jogadores se alternando.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    {
        "id": 8,
        "category": "game-cli",
        "complexity": "L2",
        "domain": "games",
        "prompt": "Crie o jogo da forca em Python no terminal com banco de palavras em portugues.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },

    # ─── L2: jogo web com JS legitimo ────────────────────────────────
    {
        "id": 9,
        "category": "game-web",
        "complexity": "L2",
        "domain": "games",
        "prompt": "Crie um pedra-papel-tesoura em HTML, CSS e JavaScript. Jogador vs computador.",
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "min_js": 1,
        },
    },

    # ─── L2: conversor com JS legitimo ───────────────────────────────
    {
        "id": 10,
        "category": "web-app",
        "complexity": "L2",
        "domain": "finance",
        "prompt": (
            "Crie um conversor de moedas (BRL, USD, EUR) em HTML, CSS e JavaScript "
            "com taxas fixas (mock — sem chamada de API)."
        ),
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "min_js": 1,
        },
    },

    # ─── L2: networking ──────────────────────────────────────────────
    {
        "id": 11,
        "category": "networking",
        "complexity": "L2",
        "domain": "dev-tools",
        "prompt": "Crie um arquivo python que sobe um HTTP server simples na porta 8000 servindo arquivos da pasta atual.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["http.server", "HTTPServer", "SimpleHTTPRequestHandler"],
        },
    },

    # ─── L2: site educacional infantil ───────────────────────────────
    {
        "id": 12,
        "category": "site-educational",
        "complexity": "L2",
        "domain": "education-kids",
        "prompt": "Crie um site infantil sobre dinossauros em HTML e CSS, com 4 especies (T-Rex, Velociraptor, Triceratops, Estegossauro), curiosidades e imagens placeholder.",
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "forbidden_exts": [".js"],
        },
    },

    # ─── L3: sistemas de negocio reais ───────────────────────────────
    {
        "id": 13,
        "category": "business-system",
        "complexity": "L3",
        "domain": "delivery",
        "prompt": (
            "Crie um sistema python de pizzaria delivery com cadastro de "
            "clientes, cardapio de pizzas, pedidos, status (preparo/saiu/entregue) "
            "e persistencia em JSON."
        ),
        "expect": {
            "min_py": 3,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    {
        "id": 14,
        "category": "business-system",
        "complexity": "L3",
        "domain": "fitness",
        "prompt": (
            "Crie um sistema python para academia: cadastro de alunos, planos "
            "de treino, controle de presenca e mensalidades. Persistencia SQLite."
        ),
        "expect": {
            "min_py": 3,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["sqlite3", "import sqlite"],
        },
    },
    {
        "id": 15,
        "category": "business-system",
        "complexity": "L3",
        "domain": "entertainment",
        "prompt": (
            "Crie um sistema python para cinema: gestao de filmes, sessoes, "
            "vendas de ingresso e relatorio de bilheteria. Persistencia JSON."
        ),
        "expect": {
            "min_py": 3,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    {
        "id": 16,
        "category": "business-system",
        "complexity": "L3",
        "domain": "finance",
        "prompt": (
            "Crie um sistema bancario simples em Python: criar conta, "
            "deposito, saque, transferencia, extrato. Persistencia JSON, "
            "validacoes de saldo e tratamento de erros."
        ),
        "expect": {
            "min_py": 3,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },

    # ─── L3: API e web-app integrado ─────────────────────────────────
    {
        "id": 17,
        "category": "web-app-fullstack",
        "complexity": "L3",
        "domain": "productivity",
        "prompt": (
            "Crie um app de TODO list completo: backend Python Flask com API REST "
            "(GET, POST, DELETE de tarefas) e frontend HTML+CSS+JS que consome a API. "
            "Persistencia em JSON."
        ),
        "expect": {
            "min_py": 1,
            "min_html": 1,
            "must_contain_any": ["Flask", "from flask", "import flask"],
        },
    },

    # ─── L2: receitas com filtro JS ──────────────────────────────────
    {
        "id": 18,
        "category": "web-app",
        "complexity": "L2",
        "domain": "food",
        "prompt": (
            "Crie um site de receitas em HTML, CSS e JavaScript com pelo menos 6 receitas "
            "e filtro por categoria (massa, carne, doce, vegano)."
        ),
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "min_js": 1,
        },
    },
]


def _files_of_ext(text, ext_pattern):
    """Captura arquivos com a extensao dada, filtra frameworks (Node.js etc)."""
    pattern = r"""['"]([A-Za-z0-9_/.\-]+\.""" + ext_pattern + r""")['"]"""
    captured = set(re.findall(pattern, text))
    real_files = set()
    for f in captured:
        basename = f.rsplit("/", 1)[-1]
        if basename and basename[0].isupper():
            continue  # framework name no conteudo
        real_files.add(f)
    return real_files


def run_one(agent, task):
    t0 = time.time()
    print(f"\n{'='*72}")
    print(f"#{task['id']:2} [{task['complexity']}/{task['category']}/{task['domain']}]")
    print(f"     {task['prompt']}")
    print('='*72)

    try:
        result = agent.plan(task["prompt"])
    except Exception as e:
        return {
            "task_id": task["id"], "passed": False,
            "error": f"excecao: {e}", "elapsed_s": round(time.time() - t0, 1),
        }

    elapsed = time.time() - t0
    m = {
        "task_id": task["id"],
        "category": task["category"],
        "complexity": task["complexity"],
        "domain": task["domain"],
        "prompt": task["prompt"],
        "elapsed_s": round(elapsed, 1),
        "n_steps": len(result.get("steps", [])),
        "error": result.get("error", ""),
    }

    if not result.get("steps"):
        m["passed"] = False
        print(f"\n[FAIL] tempo={m['elapsed_s']}s | sem steps")
        if m.get("error"):
            print(f"      ❌ {m['error'][:120]}")
        return m

    first_code = result["steps"][0].get("params", {}).get("code", "")
    m["total_code_chars"] = sum(
        len(s.get("params", {}).get("code", ""))
        for s in result["steps"]
    )

    py_set = {f for f in _files_of_ext(first_code, "py") if not f.endswith("__init__.py")}
    js_set = _files_of_ext(first_code, "js")
    css_set = _files_of_ext(first_code, "css")
    html_set = _files_of_ext(first_code, "html?") | _files_of_ext(first_code, "html")

    m["py_files"] = sorted(py_set)
    m["js_files"] = sorted(js_set)
    m["css_files"] = sorted(css_set)
    m["html_files"] = sorted(html_set)

    exp = task["expect"]
    issues = []

    for ext in exp.get("forbidden_exts", []):
        bucket = {".py": py_set, ".js": js_set, ".css": css_set, ".html": html_set}.get(ext, set())
        if bucket:
            issues.append(f"gerou {ext} proibido: {sorted(bucket)}")

    for key, count, label in [
        ("min_py", len(py_set), ".py"),
        ("min_html", len(html_set), ".html"),
        ("min_css", len(css_set), ".css"),
        ("min_js", len(js_set), ".js"),
    ]:
        if key in exp and count < exp[key]:
            issues.append(f"poucos {label}: got {count}, min {exp[key]}")

    if "max_files" in exp:
        total = len(py_set | js_set | css_set | html_set)
        if total > exp["max_files"]:
            issues.append(f"muitos arquivos: got {total}, max {exp['max_files']}")

    if "must_contain_any" in exp:
        found = any(s.lower() in first_code.lower() for s in exp["must_contain_any"])
        if not found:
            issues.append(f"nenhum dos esperados: {exp['must_contain_any']}")

    m["issues"] = issues
    m["passed"] = len(issues) == 0

    status = "PASS" if m["passed"] else "FAIL"
    print(f"\n[{status}] tempo={m['elapsed_s']}s | steps={m['n_steps']} | "
          f"code_chars={m['total_code_chars']}")
    print(f"      py={m['py_files']}")
    print(f"      html={m['html_files']} css={m['css_files']} js={m['js_files']}")
    for i in issues:
        print(f"      ⚠ {i}")
    if m.get("error"):
        print(f"      ❌ {m['error'][:120]}")

    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="roda apenas as 6 primeiras tarefas")
    parser.add_argument("--filter", default="",
                        help="filtra por categoria/complexidade/dominio")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERRO: ANTHROPIC_API_KEY nao configurada")
        sys.exit(1)

    tasks = TASKS[:6] if args.quick else TASKS
    if args.filter:
        f = args.filter.lower()
        tasks = [t for t in tasks
                 if f in t["category"] or f in t["complexity"].lower() or f in t["domain"]]

    print(f"\nSuite CRIATIVA — {len(tasks)} tarefas\n")
    agent = CodeAgent()

    results = []
    for t in tasks:
        results.append(run_one(agent, t))

    print(f"\n{'='*72}")
    print("SUMARIO")
    print('='*72)
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    pct = 100 * passed // total if total else 0
    print(f"Taxa: {passed}/{total} ({pct}%)\n")

    by_cat = {}
    for r in results:
        cat = r.get("category", "unknown")
        by_cat.setdefault(cat, {"pass": 0, "total": 0})
        by_cat[cat]["total"] += 1
        if r.get("passed"):
            by_cat[cat]["pass"] += 1

    print("Por categoria:")
    for cat, c in sorted(by_cat.items()):
        print(f"  {cat:30}  {c['pass']}/{c['total']}")
    print()

    by_complex = {}
    for r in results:
        c = r.get("complexity", "?")
        by_complex.setdefault(c, {"pass": 0, "total": 0})
        by_complex[c]["total"] += 1
        if r.get("passed"):
            by_complex[c]["pass"] += 1
    print("Por complexidade:")
    for k in sorted(by_complex.keys()):
        c = by_complex[k]
        print(f"  {k:5}  {c['pass']}/{c['total']}")
    print()

    for r in results:
        status = "✅" if r.get("passed") else "❌"
        prompt = r.get("prompt", "")[:55]
        print(f"  {status} #{r['task_id']:2}  {prompt}")

    out_dir = INNER_DIR / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"creative_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "ran_at": datetime.now().isoformat(),
            "summary": {"passed": passed, "total": total, "rate": passed/total if total else 0},
            "by_category": by_cat,
            "by_complexity": by_complex,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo em: {out_file}")

    wf_dir = INNER_DIR / "memory" / "workflows"
    if wf_dir.exists():
        valid = sum(1 for f in wf_dir.glob("code_*.json") if f.stat().st_size > 100)
        print(f"Workflows code_*.json em memory/workflows/: {valid}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
