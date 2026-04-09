"""
WebAgent v12 — Migrado para BaseAgent.
Especialista em navegação web via Playwright.
"""

import json
from agents.base_agent import BaseAgent

SYSTEM_PROMPT = (
    "Voce e o WEB AGENT — especialista em Playwright.\n"
    "NUNCA use open_app para browser. web_goto ja abre automaticamente.\n\n"
    "ACOES: web_goto(url) | web_type(field, text) | web_click(target)\n"
    "       web_key(key) | web_read() | web_new_tab(url) | wait(seconds)\n\n"
    "REGRAS:\n"
    "- SEMPRE wait(1.5) apos web_goto antes de interagir\n"
    "- Se aparecer popup de cookies, web_click('Aceitar') ou web_click('Accept')\n"
    "- Se web_click falha, tente texto parcial\n"
    "- Maximo 8 passos. JSON puro.\n\n"
    "EXEMPLOS COMPLETOS:\n\n"
    "Tarefa: 'pesquise no google sobre inteligencia artificial'\n"
    '{"steps":[\n'
    '  {"step":1,"action":"web_goto","params":{"url":"https://www.google.com"},"description":"Abrir Google"},\n'
    '  {"step":2,"action":"wait","params":{"seconds":1.5},"description":"Aguardar"},\n'
    '  {"step":3,"action":"web_type","params":{"field":"textarea[name=q]","text":"inteligencia artificial"},"description":"Digitar busca"},\n'
    '  {"step":4,"action":"web_key","params":{"key":"Enter"},"description":"Pesquisar"},\n'
    '  {"step":5,"action":"wait","params":{"seconds":2},"description":"Aguardar resultados"}\n'
    "]}\n\n"
    "Tarefa: 'entre no youtube e pesquise lofi'\n"
    '{"steps":[\n'
    '  {"step":1,"action":"web_goto","params":{"url":"https://www.youtube.com"},"description":"Abrir YouTube"},\n'
    '  {"step":2,"action":"wait","params":{"seconds":2},"description":"Aguardar"},\n'
    '  {"step":3,"action":"web_type","params":{"field":"input#search","text":"lofi"},"description":"Digitar busca"},\n'
    '  {"step":4,"action":"web_key","params":{"key":"Enter"},"description":"Pesquisar"},\n'
    '  {"step":5,"action":"wait","params":{"seconds":2},"description":"Aguardar resultados"}\n'
    "]}\n\n"
    'FORMATO: {"steps":[{"step":1,"description":"...","action":"...","params":{}}]}'
)


class WebAgent(BaseAgent):
    """Agente especialista em navegação web."""

    def __init__(self):
        super().__init__(name="WEB", system_prompt=SYSTEM_PROMPT)

    def plan(self, task, context=None):
        """Gera plano de navegação web."""
        task_text = self._extract_task_text(task)

        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)

        try:
            raw = self._client.message(
                model=self.model,
                system=self.system_prompt,
                user_content=f"TAREFA: {task_text}{ctx}\nJSON puro.",
                max_tokens=2000,
            )
            from core.json_validator import safe_parse
            plan = safe_parse(raw, self.model)

            for st in plan.get("steps", []):
                st["agent"] = "WEB"

            self.logger.info(f"Plano: {len(plan.get('steps', []))} steps")
            self._metrics["total_plans"] += 1
            self._metrics["successful_plans"] += 1
            return {"steps": plan.get("steps", []), "agent": "WEB"}

        except Exception as e:
            self.logger.error(f"Erro: {e}")
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {"steps": [], "error": str(e), "agent": "WEB"}