"""
CodeAgent v21 — Senior SWE modular.

Arquitetura redesenhada (v21 vs v20):
- code_skills.py     — detecta project_type, complexity, stack, deps, topic
- code_prompts.py    — prompts modulares por tipo de projeto
- code_validators.py — sintaxe + estrutura + qualidade + tema
- code_agent.py      — orquestrador enxuto (este arquivo, ~150 linhas)

Pipeline:
    1. analyze(task) -> skills      [puro, custo zero]
    2. build_system_prompt(ptype)   [puro]
    3. build_user_message(task, skills, retry?)
    4. LLM (Sonnet/Haiku conforme skills.needs_sonnet)
    5. validate_all(code, ptype, topic) — fail-fast com motivo literal
    6. Se falhar, retry 1x com motivo como feedback
    7. Retorna steps prontos para run_python

Custo otimizado:
- Prompt focado (so o bloco do tipo detectado)
- Modelo escolhido pela analise: Haiku para prototype + static_site simples,
  Sonnet para professional / multi-arquivo / conteudo rico
"""

from __future__ import annotations

import getpass
from typing import Optional

from agents.base_agent import BaseAgent
from agents.code_skills import analyze
from agents.code_prompts import build_system_prompt, build_user_message
from agents.code_validators import validate_all
from agents.code_planner import make_plan, format_plan_for_generator
from core.config import get_config
from core.json_validator import safe_parse


# Tipos de projeto que SE BENEFICIAM do planner (multi-arquivo).
# Para static_site / python_script simples, o planner so adiciona latencia.
_PLANNER_TARGETS = {
    "python_cli", "rest_api", "fullstack_web", "python_gui",
    "python_game", "python_data", "python_bot", "interactive_site",
}


USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"

# Tokens por (complexidade, tipo). Output observado:
#   - static_site:    3-5k tokens
#   - python_cli:     8-12k tokens
#   - python_gui:    12-18k tokens (customtkinter eh volumoso)
#   - rest_api:       8-12k tokens
# Truncamento causa string nao-fechada → SyntaxError. Vale dar margem.
MAX_TOKENS_BY_COMPLEXITY = {
    "prototype":    5000,
    "small":        8000,
    "medium":      12000,
    "professional": 16000,
}

# Bonus por tipo (somado ao base). GUI multi-arquivo e o caso mais volumoso.
_TYPE_TOKEN_BONUS = {
    "python_gui":     4000,    # customtkinter + 5 arquivos pode dar 18-20k
    "fullstack_web":  3000,
    "rest_api":       2000,
    "python_game":    2000,
}


class CodeAgent(BaseAgent):
    """v21 — modular, com skills detection + validacao em camadas."""

    def __init__(self):
        # System prompt e montado dinamicamente em plan() — aqui passamos vazio
        super().__init__(name="CODE", system_prompt="")
        self._config = get_config()

    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)
        # Prefere a versao ORIGINAL do usuario (sem reformulacao do Maestro)
        # para topic extraction e theme leak validation. Maestro as vezes
        # adiciona palavras como "arquitetura modular" que poluem o tema.
        original_task = self._extract_original_task(task)
        self._last_task_text = original_task or task_text

        # ── 1. Analise (skills detection puro) ──────────────────────
        # Usamos `original_task` para evitar topic poluido quando o Maestro
        # reformulou a task com termos genericos ("arquitetura modular").
        analysis_input = original_task or task_text
        skills = analyze(analysis_input)
        self.logger.info(
            f"Skills: type={skills['project_type']} cx={skills['complexity']} "
            f"stack={skills['stack']} topic='{skills['topic']}' "
            f"deps={skills['dependencies']}"
        )

        # ── 2. Escolha de modelo ────────────────────────────────────
        model = (
            self._config.get("models.strong")
            if skills["needs_sonnet"]
            else self._config.get("models.fast")
        )
        base_tokens = MAX_TOKENS_BY_COMPLEXITY.get(skills["complexity"], 10000)
        bonus = _TYPE_TOKEN_BONUS.get(skills["project_type"], 0)
        max_tokens = base_tokens + bonus
        self.logger.info(
            f"Modelo: {'Sonnet' if skills['needs_sonnet'] else 'Haiku'} "
            f"(max_tokens={max_tokens}, base={base_tokens}+bonus={bonus})"
        )

        # ── 2.5. PLAN-THEN-GENERATE (CoT em 2 chamadas) ─────────────
        # Para projetos multi-arquivo, primeiro pedimos um ESQUELETO ao
        # Haiku. O esqueleto e validado (sem ciclos, exports/imports
        # coerentes). Se OK, e injetado no prompt do gerador como guia.
        # Reduz drasticamente "arquivos pela metade" e "imports quebrados".
        plan_hint = ""
        if skills["project_type"] in _PLANNER_TARGETS:
            planner = make_plan(task_text, skills)
            if planner["ok"]:
                plan_hint = format_plan_for_generator(planner["plan"])
                self.logger.info(
                    f"Planner: {len(planner['plan'].get('files', []))} arquivos planejados"
                )
            else:
                # Plano ruim — apenas log, segue sem hint
                self.logger.warning(f"Planner falhou (segue sem hint): {planner['reason']}")

        # ── 3-4-5. Ate 3 tentativas (1 + 2 retries) ─────────────────
        # Antes era so 1 retry (2 tentativas). Validadores em camadas
        # geram cenarios onde a 2a tentativa corrige um erro mas cria
        # outro. Com 3 tentativas o LLM converge em casos mais dificeis.
        last_reason = None
        for attempt in range(1, 4):
            feedback = last_reason if attempt > 1 else None
            if attempt > 1:
                self.logger.warning(
                    f"Retry {attempt - 1}/2: {last_reason}"
                )
            result = self._call_and_validate(
                task_text, skills, model, max_tokens,
                retry_feedback=feedback, plan_hint=plan_hint,
            )
            if result["ok"]:
                # Log warnings (qualidade nao-critica)
                for w in result.get("warnings", []):
                    self.logger.warning(f"Soft validation: {w}")
                return self._build_response(result["steps"], model)
            last_reason = result["reason"]

        # ── Falha definitiva apos 3 tentativas ───────────────────────
        self.logger.error(f"Falhou apos 3 tentativas: {last_reason}")
        self._metrics["total_plans"] += 1
        self._metrics["failed_plans"] += 1
        return {
            "steps": [],
            "agent": "CODE",
            "error": f"CodeAgent falhou: {last_reason}",
        }

    # ──────────────────────────────────────────────────────────────────

    def _call_and_validate(self, task_text: str, skills: dict, model: str,
                           max_tokens: int,
                           retry_feedback: Optional[str],
                           plan_hint: str = "") -> dict:
        """Uma rodada: monta prompt focado, chama LLM, valida em camadas."""
        system = build_system_prompt(skills["project_type"])
        user = build_user_message(task_text, skills, retry_feedback)

        # Anexa esqueleto pre-validado (se houver). Vem ANTES do
        # checklist final para o LLM ja saber a estrutura esperada.
        if plan_hint:
            user = user + "\n\n" + plan_hint

        try:
            raw = self._client.message(
                model=model,
                system=system,
                user_content=user,
                max_tokens=max_tokens,
            )
            plan = safe_parse(raw, model)
        except Exception as e:
            return {"ok": False, "reason": f"chamada LLM falhou: {e}"}

        return self._validate_and_normalize(plan, skills)

    def _validate_and_normalize(self, plan: dict, skills: dict) -> dict:
        """Aplica validate_all + normaliza steps para o orquestrador."""
        raw_steps = plan.get("steps", [])
        if not raw_steps:
            return {"ok": False, "reason": "LLM nao devolveu nenhum step"}

        ptype = skills["project_type"]
        topic = skills.get("topic", "")
        steps = []
        all_warnings: list[str] = []

        for st in raw_steps:
            code = st.get("code", "")
            code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)
            if not code.strip():
                continue

            # Pipeline completo de validacao (HARD bloqueia, SOFT vira warning)
            v = validate_all(code, ptype, topic,
                             task=getattr(self, "_last_task_text", ""))
            if not v["ok"]:
                return {"ok": False, "reason": v["reason"]}

            code = v["code"]
            all_warnings.extend(v.get("warnings", []))
            fixes = v.get("fixes_applied", {})
            if fixes.get("startfile_replaced"):
                self.logger.info(
                    f"Defesa: substitui {fixes['startfile_replaced']} "
                    "os.startfile(*.html) por webbrowser.open"
                )

            steps.append({
                "step": st.get("step", len(steps) + 1),
                "description": st.get("description", ""),
                "action": "run_python",
                "params": {"code": code,
                           "description": st.get("description", "")},
                "agent": "CODE",
            })

        if not steps:
            return {"ok": False, "reason": "todos os steps tinham code vazio"}

        return {"ok": True, "steps": steps, "reason": "",
                "warnings": all_warnings}

    def _build_response(self, steps: list, model: str) -> dict:
        model_tag = model.split("-")[1] if "-" in model else model
        total_code = sum(len(s["params"]["code"]) for s in steps)
        self.logger.info(
            f"Plano: {len(steps)} step(s) (model={model_tag}, code={total_code} chars)"
        )
        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1
        return {"steps": steps, "agent": "CODE"}


# ════════════════════════════════════════════════════════════════════
#  Backward-compat — helpers privados antigos como wrappers das APIs
#  novas em code_skills.py / code_validators.py.
#  Mantemos para nao quebrar smoke tests existentes e clientes externos.
# ════════════════════════════════════════════════════════════════════

from agents.code_skills import analyze as _analyze_task
from agents.code_validators import (
    count_files_by_ext as _count_files_by_ext,
    replace_startfile_with_webbrowser as _replace_startfile_v,
    detect_inline_program as _detect_inline_v,
)


def _needs_sonnet(task: str) -> bool:
    """Compat: retorna True se a tarefa merece Sonnet."""
    a = _analyze_task(task)
    return a["needs_sonnet"]


def _is_python_system_task(task: str) -> bool:
    """
    Compat: tarefa de sistema Python multi-arquivo.
    v21.4: aceita tanto python_cli (terminal) quanto python_gui (interface
    grafica). Antes so reconhecia CLI; agora "sistema" default e GUI.
    """
    ptype = _analyze_task(task)["project_type"]
    return ptype in ("python_cli", "python_gui")


_PYTHON_PROJECT_TYPES = {
    "python_cli", "python_script", "python_gui", "python_game",
    "python_data", "python_automation", "python_bot",
}


def _is_python_task(task: str) -> bool:
    """Compat: qualquer tarefa que envolve Python."""
    return _analyze_task(task)["project_type"] in _PYTHON_PROJECT_TYPES


def _count_py_files_in_code(code: str) -> int:
    """Compat: conta .py distintos no creator script."""
    return _count_files_by_ext(code).get(".py", 0)


def _has_startfile_html(code: str) -> bool:
    """Compat: detecta os.startfile mirando HTML."""
    if "os.startfile" not in code:
        return False
    cl = code.lower()
    return ".html" in cl or ".htm'" in cl or '.htm"' in cl


def _replace_startfile_with_webbrowser(code: str) -> tuple[str, int]:
    """Compat: alias para code_validators.replace_startfile_with_webbrowser."""
    return _replace_startfile_v(code)


def _looks_like_inline_program(code: str) -> tuple[bool, str]:
    """Compat: retorna (e_inline, motivo_curto). v5: regex aceita
    'detectei X' (sem aspas) ou \"detectei 'X'\" (com aspas)."""
    motivo = _detect_inline_v(code)
    if motivo is None:
        return False, ""
    import re as _re
    # tenta com aspas primeiro, depois sem aspas
    m = _re.search(r"detectei '([^']+)'", motivo)
    if not m:
        m = _re.search(r"detectei ([A-Z][\w/.]+ ?[\w/.]*)", motivo)
    label = m.group(1) if m else "inline"
    return True, label
