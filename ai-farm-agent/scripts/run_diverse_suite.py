"""
Suite diversificada — 15 tarefas cobrindo dominio, tech e complexidade
variados. Objetivo: expor o CODE_AGENT a contextos diferentes pra:
  - Encher memory/workflows/ com templates diversos para reuso futuro
  - Validar entendimento em cenarios fora do "site sobre X / sistema python"
  - Identificar onde o agente se perde com prompts nao-padrao

A suite cobre:
  - Sites multi-pagina, single-pagina, com/sem JS
  - Sistemas Python CLI, Tkinter, Flask (API)
  - Scripts utility (validacao CPF, gerador senhas, conversor, analise logs)
  - Dominios brasileiros (CPF, museu, escolar)
  - Especificacoes explicitas (3 paginas, com SQLite, com argparse)

Cost estimate: 15 tasks × ~$0.01 (mix Sonnet/Haiku) ≈ $0.15 total

Uso:
    cd ai-farm-agent
    python scripts/run_diverse_suite.py [--quick]

  --quick: roda apenas as 5 primeiras (smoke check de baixo custo)
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
    # ─── L1: tarefas curtas e utilitarias ────────────────────────────
    {
        "id": 1,
        "category": "utility-single-file",
        "complexity": "L1",
        "domain": "BR-data-validation",
        "prompt": "Crie um arquivo python que valida CPF e CNPJ com funcoes separadas.",
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["def validar_cpf", "def validate_cpf"],
        },
    },
    {
        "id": 2,
        "category": "utility-single-file",
        "complexity": "L1",
        "domain": "security",
        "prompt": (
            "Crie um script python que gera senhas aleatorias seguras "
            "com argumentos de linha de comando (tamanho, simbolos)."
        ),
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["argparse", "ArgumentParser"],
        },
    },
    {
        "id": 3,
        "category": "utility-single-file",
        "complexity": "L1",
        "domain": "data-analysis",
        "prompt": (
            "Crie um arquivo python que le um arquivo de log .txt e gera "
            "estatisticas: total de linhas, contagem de erros, IPs unicos."
        ),
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },

    # ─── L2: sites multi-pagina e single-pagina ──────────────────────
    {
        "id": 4,
        "category": "site-multipagina",
        "complexity": "L2",
        "domain": "culinaria",
        "prompt": (
            "Crie um site sobre receitas brasileiras com 3 paginas "
            "(index.html, receitas.html, sobre.html) em HTML e CSS."
        ),
        "expect": {
            "min_html": 3,
            "min_css": 1,
            "forbidden_exts": [".js"],
        },
    },
    {
        "id": 5,
        "category": "site-singlepage",
        "complexity": "L2",
        "domain": "portfolio",
        "prompt": (
            "Crie um portfolio de desenvolvedor em HTML e CSS com secoes "
            "projetos, skills, contato. Design moderno escuro."
        ),
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "forbidden_exts": [".js"],
        },
    },
    {
        "id": 6,
        "category": "landing-page",
        "complexity": "L2",
        "domain": "ecommerce",
        "prompt": (
            "Crie uma landing page para um produto ficticio de cafe "
            "especial em HTML e CSS, com hero, features, preco e contato."
        ),
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "forbidden_exts": [".js"],
        },
    },
    {
        "id": 7,
        "category": "site-cultural",
        "complexity": "L2",
        "domain": "BR-cultura",
        "prompt": (
            "Crie um site sobre o Museu do Ipiranga em HTML e CSS, "
            "com historia, exposicoes e visitas."
        ),
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "forbidden_exts": [".js"],
        },
    },

    # ─── L2/L3: web app com JS legitimo ──────────────────────────────
    {
        "id": 8,
        "category": "web-app-vanilla-js",
        "complexity": "L2",
        "domain": "tools",
        "prompt": (
            "Crie um conversor de unidades (km, milhas, kg, libras) "
            "em HTML, CSS e JavaScript. JS para conversao em tempo real."
        ),
        "expect": {
            "min_html": 1,
            "min_css": 1,
            "min_js": 1,
        },
    },

    # ─── L3: sistemas Python CLI multi-arquivo ───────────────────────
    {
        "id": 9,
        "category": "python-cli-system",
        "complexity": "L3",
        "domain": "library",
        "prompt": (
            "Crie um sistema python de biblioteca com cadastro de livros, "
            "emprestimo, devolucao e persistencia em SQLite."
        ),
        "expect": {
            "min_py": 3,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["sqlite3", "import sqlite"],
        },
    },
    {
        "id": 10,
        "category": "python-cli-system",
        "complexity": "L3",
        "domain": "education-BR",
        "prompt": (
            "Crie um sistema python profissional para gestao escolar com "
            "cadastro de alunos, notas, presenca e relatorios. Persistencia JSON."
        ),
        "expect": {
            "min_py": 3,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },

    # ─── L2/L3: sistemas Python com GUI (Tkinter) ────────────────────
    {
        "id": 11,
        "category": "python-tkinter",
        "complexity": "L2",
        "domain": "productivity",
        "prompt": (
            "Crie um sistema desktop em Python com Tkinter para "
            "gerenciar tarefas pessoais (adicionar, marcar como feita, deletar)."
        ),
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["tkinter", "Tk()", "customtkinter", "import tkinter"],
        },
    },
    {
        "id": 12,
        "category": "python-tkinter",
        "complexity": "L2",
        "domain": "math",
        "prompt": (
            "Crie uma calculadora cientifica em python com Tkinter, "
            "com operacoes basicas (+,-,*,/), trig (sin,cos,tan) e potencia."
        ),
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["tkinter", "import math"],
        },
    },

    # ─── L3: web framework (Flask) ───────────────────────────────────
    {
        "id": 13,
        "category": "python-flask-api",
        "complexity": "L3",
        "domain": "web-api",
        "prompt": (
            "Crie uma API REST em Flask para gerenciar usuarios "
            "(GET, POST, DELETE) com persistencia em arquivo JSON."
        ),
        "expect": {
            "min_py": 1,
            "must_contain_any": ["flask", "Flask", "from flask"],
        },
    },

    # ─── L2: utility com dependencia externa ─────────────────────────
    {
        "id": 14,
        "category": "utility-external-lib",
        "complexity": "L2",
        "domain": "tools",
        "prompt": (
            "Crie um arquivo python que gera QR code a partir de texto "
            "usando a biblioteca qrcode. Salva como PNG."
        ),
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
            "must_contain_any": ["qrcode", "import qrcode"],
        },
    },

    # ─── L1: chatbot simples ─────────────────────────────────────────
    {
        "id": 15,
        "category": "python-simple-bot",
        "complexity": "L1",
        "domain": "conversational",
        "prompt": (
            "Crie um chatbot em python que responde perguntas sobre o "
            "tempo (mock — respostas pre-definidas, nao precisa API real)."
        ),
        "expect": {
            "min_py": 1,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
]


def _files_of_ext(text, ext_pattern):
    """
    Captura nomes de arquivos com a extensao dada.

    Filtra falsos positivos comuns (Node.js / React.js / Vue.js / Next.js
    aparecem no conteudo HTML como nome de tech, nao como arquivo).
    Regras: nome de arquivo real geralmente comeca com minuscula ou eh
    'index'/'main'/'app'/etc. Nomes com maiuscula no inicio sao tipicamente
    frameworks/bibliotecas mencionados no texto.
    """
    pattern = r"""['"]([A-Za-z0-9_/.\-]+\.""" + ext_pattern + r""")['"]"""
    captured = set(re.findall(pattern, text))
    # Filtra: descarta entries que comecam com letra MAIUSCULA (provavelmente
    # nome de framework no conteudo HTML: 'Node.js', 'React.js', 'Vue.js').
    real_files = set()
    for f in captured:
        basename = f.rsplit("/", 1)[-1]
        if basename and basename[0].isupper():
            continue  # provavel framework/biblioteca no texto
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

    if "must_contain_any" in exp:
        found_any = any(s in first_code for s in exp["must_contain_any"])
        if not found_any:
            issues.append(
                f"nenhum dos esperados encontrado: {exp['must_contain_any']}"
            )

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
                        help="roda apenas as 5 primeiras tarefas")
    parser.add_argument("--filter", default="",
                        help="roda apenas tasks com categoria/complexidade casando o filtro")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERRO: ANTHROPIC_API_KEY nao configurada")
        sys.exit(1)

    tasks = TASKS[:5] if args.quick else TASKS
    if args.filter:
        f = args.filter.lower()
        tasks = [t for t in tasks
                 if f in t["category"] or f in t["complexity"].lower() or f in t["domain"]]

    print(f"\nSuite DIVERSA — {len(tasks)} tarefas\n")
    agent = CodeAgent()

    results = []
    for t in tasks:
        results.append(run_one(agent, t))

    # Sumario
    print(f"\n{'='*72}")
    print("SUMARIO")
    print('='*72)
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    print(f"Taxa: {passed}/{total} ({100*passed//total if total else 0}%)\n")

    # Por categoria
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

    # Lista
    for r in results:
        status = "✅" if r.get("passed") else "❌"
        prompt = r.get("prompt", "")[:55]
        print(f"  {status} #{r['task_id']:2}  {prompt}")

    # Salvar resultado em JSON pra historico
    out_dir = INNER_DIR / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"diverse_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "ran_at": datetime.now().isoformat(),
            "summary": {"passed": passed, "total": total, "rate": passed/total if total else 0},
            "by_category": by_cat,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo em: {out_file}")

    # Workflows aprendidos
    wf_dir = INNER_DIR / "memory" / "workflows"
    if wf_dir.exists():
        valid_workflows = sum(
            1 for f in wf_dir.glob("code_*.json")
            if f.stat().st_size > 100
        )
        print(f"Workflows code_*.json em memory/workflows/: {valid_workflows}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
