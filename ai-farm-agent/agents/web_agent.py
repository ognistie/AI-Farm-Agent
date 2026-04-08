"""
WebAgent v11 — Upgrade do v9.
MUDANCAS:
- Prompt com exemplos COMPLETOS (Google, YouTube, formularios)
- Instrucoes para lidar com cookies/popups
- wait apos navegacao
"""

import json, os
from anthropic import Anthropic
from core.json_validator import safe_parse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PROMPT = (
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


class WebAgent:
    def __init__(self):
        self.model = "claude-haiku-4-5-20251001"
        self.name = "WEB"

    def plan(self, task, context=None):
        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)
        try:
            resp = client.messages.create(model=self.model, max_tokens=2000, system=PROMPT,
                messages=[{"role": "user", "content": "TAREFA: " + str(task) + ctx + "\nJSON puro."}])
            plan = safe_parse(resp.content[0].text.strip(), self.model)
            for st in plan.get("steps", []):
                st["agent"] = "WEB"
            return {"steps": plan.get("steps", []), "agent": "WEB"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "WEB"}