"""
DataAgent v13 — Especialista Excel com skills + validacao + retry.

Skills (NOVO):
- _detect_spreadsheet_type(task) — classifica em vendas, gastos, contatos,
  inventario, calendario, alunos, agendamento, generico
- _suggest_columns(stype) — colunas tipicas por tipo
- _needs_chart(task) — detecta se a tarefa pede grafico/visualizacao
- _needs_formulas(task) — detecta SUM/AVG/COUNTIF mencionados

Validacao (NOVO):
- AST parse do codigo gerado (rejeita SyntaxError antes de executar)
- 1 retry com feedback literal do erro
- Validacao 2: garante que o codigo cria .xlsx (nao .csv, .txt, .json)

Boas praticas (NOVO):
- Logging via BaseAgent.logger
- Metricas atualizadas via metodo helper (sem manualmente)
- Imports top-level claros
"""

import ast
import json
import os
import getpass
import re
from typing import Optional

from agents.base_agent import BaseAgent
from core.json_validator import safe_parse


USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"


# ───────────────────────────────────────────────────────────────────
#  Skills: deteccao de tipo de planilha
# ───────────────────────────────────────────────────────────────────

SPREADSHEET_TYPES: dict[str, dict] = {
    "vendas": {
        "keywords": ["venda", "vendas", "faturamento", "receita", "pedido", "pedidos",
                     "comercial", "comissao", "comissão"],
        "columns": ["Data", "Cliente", "Produto", "Quantidade", "Valor Unit.", "Total"],
        "suggests_chart": True,
        "suggests_formulas": ["SUM", "AVERAGE"],
    },
    "gastos": {
        "keywords": ["gasto", "gastos", "despesa", "despesas", "orcamento", "orçamento",
                     "financeiro", "custo", "custos"],
        "columns": ["Data", "Categoria", "Descricao", "Valor", "Forma de Pagamento"],
        "suggests_chart": True,
        "suggests_formulas": ["SUM", "COUNTIF"],
    },
    "contatos": {
        "keywords": ["contato", "contatos", "agenda", "lista de contatos", "cadastro",
                     "telefone", "clientes", "fornecedores"],
        "columns": ["Nome", "Email", "Telefone", "Empresa", "Cargo", "Cidade"],
        "suggests_chart": False,
        "suggests_formulas": [],
    },
    "inventario": {
        "keywords": ["inventario", "inventário", "estoque", "produtos", "produto",
                     "almoxarifado", "patrimonio", "patrimônio"],
        "columns": ["Codigo", "Produto", "Categoria", "Quantidade", "Preco", "Valor Total"],
        "suggests_chart": True,
        "suggests_formulas": ["SUM", "COUNTIF"],
    },
    "alunos": {
        "keywords": ["aluno", "alunos", "estudante", "matricula", "escola",
                     "turma", "boletim", "notas"],
        "columns": ["Matricula", "Nome", "Turma", "Nota 1", "Nota 2", "Nota 3", "Media", "Situacao"],
        "suggests_chart": True,
        "suggests_formulas": ["AVERAGE", "IF"],
    },
    "agendamento": {
        "keywords": ["agendamento", "agenda", "consulta", "consultas", "horario",
                     "horário", "reserva", "reservas"],
        "columns": ["Data", "Horario", "Cliente", "Servico", "Profissional", "Status"],
        "suggests_chart": False,
        "suggests_formulas": ["COUNTIF"],
    },
    "calendario": {
        "keywords": ["calendario", "calendário", "evento", "eventos", "atividades",
                     "cronograma"],
        "columns": ["Data", "Evento", "Local", "Responsavel", "Status"],
        "suggests_chart": False,
        "suggests_formulas": [],
    },
}


def _detect_spreadsheet_type(task: str) -> Optional[str]:
    """Retorna o tipo detectado ou None (generico)."""
    t = task.lower()
    best, best_score = None, 0
    for stype, meta in SPREADSHEET_TYPES.items():
        score = sum(1 for kw in meta["keywords"] if kw in t)
        if score > best_score:
            best_score = score
            best = stype
    return best if best_score > 0 else None


def _needs_chart(task: str) -> bool:
    t = task.lower()
    return any(w in t for w in ("grafico", "gráfico", "chart", "visualizacao",
                                 "visualização", "dashboard"))


def _needs_formulas(task: str) -> list[str]:
    t = task.lower()
    formulas = []
    if any(w in t for w in ("soma", "total", "somar")): formulas.append("SUM")
    if any(w in t for w in ("media", "média", "average")): formulas.append("AVERAGE")
    if any(w in t for w in ("contar", "count", "quantos", "quantas")): formulas.append("COUNT/COUNTIF")
    if any(w in t for w in ("maximo", "máximo", "max")): formulas.append("MAX")
    if any(w in t for w in ("minimo", "mínimo", "min")): formulas.append("MIN")
    return formulas


# ───────────────────────────────────────────────────────────────────
#  Prompt
# ───────────────────────────────────────────────────────────────────

BASE_PROMPT = """Voce e o DATA AGENT — Senior Data Engineer em Excel com Python.
Seu codigo funciona na PRIMEIRA tentativa. Sintaxe valida sempre.

REGRAS:
1. Imports: import os, subprocess; from openpyxl import Workbook
   Se grafico: from openpyxl.chart import BarChart, LineChart, Reference
   Se estilos: from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
2. Caminho: os.path.join(os.path.expanduser('~'), 'Desktop', '<nome>.xlsx')
3. NOME do arquivo: derive da tarefa (ex: vendas_q1.xlsx). NUNCA 'planilha.xlsx' generico.
4. COLISAO: antes de wb.save(filepath), se os.path.exists, salve como nome_2.xlsx.
5. Formate cabecalhos: negrito, branco em fill #1F4E79, centralizado, bordas.
6. Auto-ajuste de largura de colunas.
7. Abra no final: subprocess.Popen(f'start \"\" \"{filepath}\"', shell=True)
8. SEMPRE print() do filepath final salvo.
9. UMA step com codigo COMPLETO. Sintaxe Python valida.
10. JSON puro, sem markdown.

FORMATO: {"steps":[{"step":1,"description":"...","code":"codigo completo"}]}
"""


def _hint_for_type(stype: Optional[str], wants_chart: bool, formulas: list[str]) -> str:
    """Gera um bloco extra de hint baseado nos skills detectados."""
    if not stype and not wants_chart and not formulas:
        return ""
    parts = ["\n=== SKILLS DETECTADOS PARA ESTA TAREFA ==="]
    if stype:
        meta = SPREADSHEET_TYPES[stype]
        parts.append(f"Tipo: {stype.upper()}")
        parts.append(f"Colunas tipicas: {meta['columns']}")
    if wants_chart:
        parts.append("Grafico solicitado: adicione BarChart ou LineChart.")
        parts.append("Use: chart = BarChart(); chart.add_data(Reference(ws, ...))")
        parts.append("Anexe: ws.add_chart(chart, 'F2')")
    if formulas:
        parts.append(f"Formulas sugeridas: {formulas}")
        parts.append("Use celulas com =SUM(B2:B10), =AVERAGE(C2:C10), etc.")
    parts.append("=" * 45)
    return "\n".join(parts)


# ───────────────────────────────────────────────────────────────────
#  Agent
# ───────────────────────────────────────────────────────────────────


class DataAgent(BaseAgent):
    """Agente especialista em dados e Excel com skills + validacao."""

    def __init__(self):
        super().__init__(name="DATA", system_prompt=BASE_PROMPT)

    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)

        # Skills
        stype = _detect_spreadsheet_type(task_text)
        wants_chart = _needs_chart(task_text)
        formulas = _needs_formulas(task_text)
        if stype or wants_chart or formulas:
            self.logger.info(
                f"Skills: tipo={stype} chart={wants_chart} formulas={formulas}"
            )

        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)
        hint = _hint_for_type(stype, wants_chart, formulas)

        result = self._call_and_validate(task_text + ctx + hint, retry_feedback=None)
        if result["ok"]:
            return self._wrap_steps(result["steps"])

        # 1 retry com feedback do erro
        self.logger.warning(f"Retry com feedback: {result['reason']}")
        result = self._call_and_validate(task_text + ctx + hint,
                                         retry_feedback=result["reason"])
        if result["ok"]:
            return self._wrap_steps(result["steps"])

        # Falhou
        self.logger.error(f"Falhou apos 2 tentativas: {result['reason']}")
        self._metrics["total_plans"] += 1
        self._metrics["failed_plans"] += 1
        return {"steps": [], "error": result["reason"], "agent": "DATA"}

    # ── Internos ──────────────────────────────────────────────────

    def _call_and_validate(self, user_input: str,
                           retry_feedback: Optional[str]) -> dict:
        message = f"TAREFA: {user_input}\nJSON puro."
        if retry_feedback:
            message = (
                f"TAREFA: {user_input}\n\n"
                f"⚠️ TENTATIVA ANTERIOR FALHOU. MOTIVO:\n{retry_feedback}\n"
                "Corrija isso AGORA. JSON puro."
            )

        try:
            raw = self._client.message(
                model=self.model,
                system=self.system_prompt,
                user_content=message,
                max_tokens=4000,
            )
            plan = safe_parse(raw, self.model)
        except Exception as e:
            return {"ok": False, "reason": f"chamada LLM falhou: {e}"}

        steps_raw = plan.get("steps", [])
        if not steps_raw:
            return {"ok": False, "reason": "LLM nao retornou nenhum step"}

        steps = []
        for st in steps_raw:
            code = st.get("code", "")
            code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)

            # Validacao 1: AST parse
            try:
                ast.parse(code)
            except SyntaxError as e:
                snippet = ""
                try:
                    snippet = code.split("\n")[(e.lineno or 1) - 1][:120]
                except Exception:
                    pass
                return {
                    "ok": False,
                    "reason": (f"SyntaxError linha {e.lineno}: {e.msg}. "
                               f"Linha: `{snippet}`"),
                }

            # Validacao 2: precisa salvar .xlsx
            if ".xlsx" not in code:
                return {
                    "ok": False,
                    "reason": "codigo nao salva nenhum arquivo .xlsx",
                }

            steps.append({
                "step": st.get("step", len(steps) + 1),
                "description": st.get("description", ""),
                "action": "run_python",
                "params": {"code": code,
                           "description": st.get("description", "")},
                "agent": "DATA",
            })

        return {"ok": True, "steps": steps, "reason": ""}

    def _wrap_steps(self, steps: list) -> dict:
        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1
        total_code = sum(len(s["params"]["code"]) for s in steps)
        self.logger.info(f"Plano: {len(steps)} step(s), {total_code} chars")
        return {"steps": steps, "agent": "DATA"}
