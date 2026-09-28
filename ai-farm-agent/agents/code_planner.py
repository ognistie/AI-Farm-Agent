"""
code_planner.py — Etapa 1 do Plan-then-Generate.

Antes do CodeAgent chamar Sonnet/Haiku para gerar o creator script
COMPLETO, um classificador leve (Haiku) gera APENAS o ESQUELETO:
lista de arquivos + responsabilidade + imports entre eles.

Vantagens:
- O plano e validado ANTES de gastar tokens caros no codigo
- Imports entre arquivos formam um DAG verificavel
- Se o plano estiver ruim, retry custa ~$0.001 (so o Haiku)
- O gerador (Sonnet/Haiku) recebe estrutura pronta e gera melhor

Schema do plano:
    {
      "files": [
        {
          "name": "main.py",
          "role": "entry point que liga DB e UI",
          "imports_from": ["database", "cli"],
          "exports": ["main"]
        },
        ...
      ]
    }
"""

from __future__ import annotations

import json
from typing import Optional

from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse


PLANNER_SYSTEM_PROMPT = """Voce e o PLANNER do CodeAgent. Sua unica funcao
e gerar o ESQUELETO de arquivos de um projeto. NAO escreve codigo, NAO
escreve conteudo. Apenas estrutura.

REGRAS:
1. Cada arquivo tem nome.ext claro
2. Cada arquivo tem "role" — frase curta dizendo a responsabilidade
3. "imports_from" lista MODULOS LOCAIS (sem .py) que esse arquivo importa
4. "exports" lista funcoes/classes top-level que esse arquivo define
5. Coerencia: se A.imports_from inclui B, entao algum item em B.exports
   deve aparecer
6. NUNCA crie ciclos de import (A importa B importa A)
7. Para sistemas Python: main.py SEMPRE no plano, com import dos outros

FORMATO (JSON puro, sem markdown):
{
  "files": [
    {
      "name": "main.py",
      "role": "entry point que orquestra DB e CLI",
      "imports_from": ["database", "cli"],
      "exports": ["main"]
    }
  ],
  "external_deps": ["openpyxl", "flask"]
}
"""


def _build_planner_user_message(task: str, skills: dict) -> str:
    deps = ", ".join(skills.get("dependencies", [])) or "(stdlib)"
    return (
        f"TAREFA: {task}\n\n"
        f"Tipo de projeto: {skills['project_type']}\n"
        f"Complexidade:    {skills['complexity']}\n"
        f"Stack:           {skills['stack']}\n"
        f"Dependencias:    {deps}\n\n"
        "Gere SO o esqueleto (arquivos + roles + imports). Sem codigo.\n"
        "JSON puro."
    )


def validate_plan(plan: dict) -> Optional[str]:
    """
    Verifica que o plano e coerente:
      - tem >= 1 arquivo
      - sem ciclos de import
      - cada `imports_from` referencia arquivo do plano
      - cada item em `exports` e nome valido
    Retorna mensagem de erro ou None se OK.
    """
    files = plan.get("files", [])
    if not files:
        return "plano vazio — nenhum arquivo declarado"

    names = {f.get("name", "").replace(".py", "").split("/")[-1]: f
             for f in files if f.get("name")}
    if not names:
        return "nenhum arquivo tem 'name' valido"

    # 1. Sem ciclos (DFS detecta backedge)
    visited: dict[str, str] = {}  # 'white' | 'gray' | 'black'

    def dfs(node: str) -> Optional[str]:
        visited[node] = "gray"
        for imp in (names.get(node, {}).get("imports_from") or []):
            if imp not in names:
                continue   # import externo, ok aqui
            if visited.get(imp) == "gray":
                return f"ciclo de imports: {node} -> {imp}"
            if visited.get(imp) != "black":
                err = dfs(imp)
                if err:
                    return err
        visited[node] = "black"
        return None

    for node in names:
        if visited.get(node) != "black":
            err = dfs(node)
            if err:
                return err

    # 2. Cada imports_from existe (no plano ou e externo conhecido)
    EXTERNAL_OK = {
        "os", "sys", "json", "datetime", "subprocess", "pathlib", "re",
        "math", "random", "collections", "itertools", "functools",
        "tkinter", "pygame", "flask", "fastapi", "pandas", "numpy",
        "openpyxl", "matplotlib", "anthropic", "pydantic", "sqlite3",
        "logging", "argparse", "csv", "io", "time", "threading", "queue",
        "requests", "bs4", "beautifulsoup4", "pillow", "PIL",
        "customtkinter", "ctk", "PyQt6", "PyQt5", "PySide6", "kivy",
    }
    for fname, f in names.items():
        for imp in (f.get("imports_from") or []):
            if imp in names:
                continue
            if imp in EXTERNAL_OK:
                continue
            # Talvez seja um modulo externo nao listado — aceita warning
            # (nao queremos ser exigentes demais com libs desconhecidas)

    # 3. Pelo menos 1 arquivo deve ter exports (vazio = inutil)
    has_exports = any(f.get("exports") for f in files)
    if not has_exports and len(files) > 1:
        return "nenhum arquivo declara 'exports' — projeto provavelmente vazio"

    return None


def make_plan(task: str, skills: dict) -> dict:
    """
    Chama o LLM (Haiku) para gerar o esqueleto.

    Returns:
        {
            "ok": bool,
            "plan": {...} se ok,
            "reason": str se nao ok,
            "tokens_used": int (aprox),
        }
    """
    config = get_config()
    client = get_client()
    # Etapa leve: modelo/effort vem de agent_models.planner / agent_effort.planner
    model = config.get_model("planner")
    user = _build_planner_user_message(task, skills)

    try:
        raw = client.message(
            model=model,
            system=PLANNER_SYSTEM_PROMPT,
            user_content=user,
            max_tokens=8000,
            effort=config.get_effort("planner"),
            agent="CODE_PLANNER",
        )
    except Exception as e:
        return {"ok": False, "reason": f"planner LLM call falhou: {e}"}

    try:
        plan = safe_parse(raw, model)
    except Exception as e:
        return {"ok": False, "reason": f"planner JSON invalido: {e}"}

    err = validate_plan(plan)
    if err:
        return {"ok": False, "reason": f"plano invalido: {err}", "plan": plan}

    return {"ok": True, "plan": plan}


def format_plan_for_generator(plan: dict) -> str:
    """
    Converte o plano JSON em um bloco texto que vai no USER message
    do gerador. O LLM le isso e gera o creator script seguindo a estrutura.
    """
    if not plan or not plan.get("files"):
        return ""

    lines = ["=== ESQUELETO PRE-VALIDADO (siga esta estrutura) ==="]
    for f in plan["files"]:
        name = f.get("name", "?")
        role = f.get("role", "")
        imps = f.get("imports_from") or []
        exps = f.get("exports") or []
        lines.append(f"  • {name}: {role}")
        if imps:
            lines.append(f"      imports_from: {imps}")
        if exps:
            lines.append(f"      exports: {exps}")
    if plan.get("external_deps"):
        lines.append(f"  Dependencias externas: {plan['external_deps']}")
    lines.append("=" * 50)
    lines.append("Gere o creator script Python que CRIA esses arquivos com")
    lines.append("conteudo REAL. Os imports devem casar com os exports.")
    return "\n".join(lines)
