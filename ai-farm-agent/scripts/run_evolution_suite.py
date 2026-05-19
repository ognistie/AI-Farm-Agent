"""
Suite de evolucao do CODE_AGENT — roda 5 tarefas variadas com a API real
para o agente APRENDER (salvar workflows na memoria) e medir taxa de sucesso.

Pre-requisito: ANTHROPIC_API_KEY no .env (que pode estar na pasta interna
ou na pasta-raiz do repo — o script procura nos dois lugares).

Uso:
    cd ai-farm-agent
    python scripts/run_evolution_suite.py
"""

import os
import sys
import time
from pathlib import Path

# Resolve paths relativo a este script (funciona de qualquer CWD)
SCRIPT_DIR = Path(__file__).resolve().parent
INNER_DIR = SCRIPT_DIR.parent           # ai-farm-agent/ai-farm-agent
OUTER_DIR = INNER_DIR.parent             # ai-farm-agent (raiz do repo)

# Carrega .env — procura primeiro na pasta-interna, depois na raiz
try:
    from dotenv import load_dotenv
    loaded_from = None
    for env_path in (INNER_DIR / ".env", OUTER_DIR / ".env"):
        if env_path.exists():
            # override=True garante que sobrescreve variaveis vazias do shell
            load_dotenv(str(env_path), override=True)
            loaded_from = env_path
            break
    if loaded_from:
        print(f"[suite] .env carregado de {loaded_from}")
    else:
        print("[suite] WARN: .env nao encontrado em ai-farm-agent/ nem na raiz")
except ImportError:
    print("[suite] WARN: python-dotenv nao instalado — usando env do shell")

sys.path.insert(0, str(INNER_DIR))

from agents.code_agent import CodeAgent


TASKS = [
    {
        "id": 1,
        "prompt": "Abra o VS Code e crie um site profissional sobre budismo.",
        "expect": {
            "task_type": "html_css(_js)_site",
            "min_files": 2,
            "forbidden_exts": [],
        },
    },
    {
        "id": 2,
        "prompt": "Abra o VS Code e crie dois arquivos HTML e CSS de um site de skate 90s.",
        "expect": {
            "task_type": "html_css_strict",
            "exact_files": 2,
            "forbidden_exts": [".js"],
        },
    },
    {
        "id": 3,
        "prompt": "Abra o VS Code e crie um sistema profissional em Python de agendamento de consulta no dentista.",
        "expect": {
            "task_type": "python_system",
            "min_py_files": 4,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    {
        "id": 4,
        "prompt": "Crie um site so com HTML e CSS sobre tecnologia.",
        "expect": {
            "task_type": "html_css_strict",
            "forbidden_exts": [".js"],
        },
    },
    {
        "id": 5,
        "prompt": "Crie um sistema Python simples de cadastro de alunos.",
        "expect": {
            "task_type": "python_system",
            "min_py_files": 2,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    # Extras pra variar dominio e enriquecer a memoria
    {
        "id": 6,
        "prompt": "Crie um site em HTML e CSS sobre cafe especial.",
        "expect": {
            "task_type": "html_css_strict",
            "forbidden_exts": [".js"],
        },
    },
    {
        "id": 7,
        "prompt": "Crie um sistema em Python de controle de estoque de farmacia.",
        "expect": {
            "task_type": "python_system",
            "min_py_files": 3,
            "forbidden_exts": [".html", ".css", ".js"],
        },
    },
    {
        "id": 8,
        "prompt": "Crie um arquivo python que converte CSV para JSON.",
        "expect": {
            "task_type": "single_file_python",
            "min_py_files": 1,
        },
    },
]


def run_one(agent: CodeAgent, task: dict) -> dict:
    """Roda 1 tarefa e devolve metricas."""
    t0 = time.time()
    print(f"\n{'='*70}")
    print(f"TAREFA #{task['id']}: {task['prompt']}")
    print('='*70)

    result = agent.plan(task["prompt"])
    elapsed = time.time() - t0

    metrics = {
        "task_id": task["id"],
        "prompt": task["prompt"],
        "elapsed_s": round(elapsed, 1),
        "n_steps": len(result.get("steps", [])),
        "has_error": "error" in result,
        "error": result.get("error", ""),
    }

    if result.get("steps"):
        total_code = sum(
            len(s.get("params", {}).get("code", ""))
            for s in result["steps"]
        )
        metrics["total_code_chars"] = total_code

        # Analise estatica do creator script — conta arquivos DISTINTOS,
        # nao referencias (resolve "got 5" quando agente criou 2 e referenciou 5x)
        import re as _re
        first_code = result["steps"][0].get("params", {}).get("code", "")

        def _files_of_ext(text, ext):
            # captura "X.ext" ou 'X.ext' como string literal
            pattern = r"""['"]([A-Za-z0-9_/.\-]+\.""" + ext + r""")['"]"""
            return set(_re.findall(pattern, text))

        py_set = {f for f in _files_of_ext(first_code, "py") if not f.endswith("__init__.py")}
        js_set = _files_of_ext(first_code, "js")
        css_set = _files_of_ext(first_code, "css")
        html_set = _files_of_ext(first_code, "html?") | _files_of_ext(first_code, "html")

        metrics["py_files"] = sorted(py_set)
        metrics["js_files"] = sorted(js_set)
        metrics["css_files"] = sorted(css_set)
        metrics["html_files"] = sorted(html_set)

        # Avalia regras do expect — contagens com set (distintos)
        exp = task["expect"]
        issues = []
        if "forbidden_exts" in exp:
            for ext in exp["forbidden_exts"]:
                if ext == ".js" and js_set:
                    issues.append(f"gerou .js mesmo proibido: {sorted(js_set)}")
                if ext == ".html" and html_set:
                    issues.append(f"gerou .html mesmo proibido: {sorted(html_set)}")
                if ext == ".css" and css_set:
                    issues.append(f"gerou .css mesmo proibido: {sorted(css_set)}")
        if "min_py_files" in exp:
            if len(py_set) < exp["min_py_files"]:
                issues.append(
                    f"poucos arquivos .py: {sorted(py_set)} (min={exp['min_py_files']})"
                )
        if "exact_files" in exp:
            total_files = py_set | js_set | css_set | html_set
            if len(total_files) != exp["exact_files"]:
                issues.append(
                    f"esperado {exp['exact_files']} arquivos distintos, "
                    f"got {len(total_files)}: {sorted(total_files)}"
                )
        metrics["issues"] = issues
        metrics["passed"] = len(issues) == 0
    else:
        metrics["passed"] = False

    # Print resumo
    status = "PASS" if metrics.get("passed") else "FAIL"
    print(f"\n[{status}] tempo={metrics['elapsed_s']}s | steps={metrics['n_steps']} | "
          f"code_chars={metrics.get('total_code_chars', 0)}")
    if "py_files" in metrics:
        print(f"       py={metrics['py_files']}")
        print(f"       css={metrics['css_files']} js={metrics['js_files']} html={metrics['html_files']}")
    if metrics.get("issues"):
        for i in metrics["issues"]:
            print(f"       ⚠ {i}")
    if metrics.get("error"):
        print(f"       ❌ ERRO: {metrics['error'][:120]}")

    return metrics


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERRO: ANTHROPIC_API_KEY nao configurada no .env")
        sys.exit(1)

    print(f"\nSuite de evolucao do CODE_AGENT — {len(TASKS)} tarefas\n")
    agent = CodeAgent()

    all_metrics = []
    for task in TASKS:
        try:
            m = run_one(agent, task)
            all_metrics.append(m)
        except Exception as e:
            print(f"❌ EXCECAO na tarefa #{task['id']}: {e}")
            all_metrics.append({
                "task_id": task["id"], "passed": False, "error": str(e),
            })

    # Sumario final
    print(f"\n{'='*70}")
    print("SUMARIO DA SUITE")
    print('='*70)
    passed = sum(1 for m in all_metrics if m.get("passed"))
    total = len(all_metrics)
    print(f"Taxa de sucesso: {passed}/{total} ({100*passed//total}%)")
    print()
    for m in all_metrics:
        status = "✅" if m.get("passed") else "❌"
        prompt = m.get("prompt", "")[:60]
        print(f"  {status} #{m['task_id']:2}  {prompt}")

    # Workflows aprendidos
    from pathlib import Path
    wf = Path("memory/workflows")
    if wf.exists():
        new_today = [
            f for f in wf.glob("code_*.json")
            if "2026" in f.name  # ajuste o ano conforme necessario
        ]
        print(f"\nWorkflows code_*.json em memory/workflows/: {len(new_today)}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
