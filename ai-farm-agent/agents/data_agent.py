"""
DataAgent v11 — Upgrade do v9.
MUDANCAS: Prompt limpo, template mantido (ja funcionava bem).
"""

import json, os, getpass
from anthropic import Anthropic
from core.json_validator import safe_parse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
USERNAME = getpass.getuser()
BASE = "C:/Users/" + USERNAME

PROMPT = (
    "Voce e o DATA AGENT — especialista senior em Excel com Python.\n"
    "Seu codigo funciona na PRIMEIRA tentativa.\n\n"
    "REGRAS:\n"
    "1. SEMPRE imports: import os, subprocess, openpyxl, etc\n"
    "2. Caminho: os.path.join(os.path.expanduser('~'), 'Desktop', 'arquivo.xlsx')\n"
    "3. Formate cabecalhos: negrito, cor azul, centralizado, bordas\n"
    "4. Auto-ajuste largura colunas\n"
    "5. Abra no final: subprocess.Popen(f'start \"\" \"{filepath}\"', shell=True)\n"
    "6. SEMPRE print() resultado\n"
    "7. UMA step com codigo COMPLETO\n\n"
    "TEMPLATE:\n"
    "import os, subprocess\n"
    "from openpyxl import Workbook\n"
    "from openpyxl.styles import Font, PatternFill, Alignment, Border, Side\n"
    "from openpyxl.utils import get_column_letter\n\n"
    "desktop = os.path.join(os.path.expanduser('~'), 'Desktop')\n"
    "filepath = os.path.join(desktop, 'planilha.xlsx')\n"
    "wb = Workbook()\n"
    "ws = wb.active\n"
    "ws.title = 'Dados'\n\n"
    "hdr_font = Font(bold=True, color='FFFFFF', size=11)\n"
    "hdr_fill = PatternFill('solid', fgColor='1F4E79')\n"
    "thin = Side(style='thin')\n"
    "border = Border(left=thin, right=thin, top=thin, bottom=thin)\n\n"
    "headers = ['Col1', 'Col2']\n"
    "for col, h in enumerate(headers, 1):\n"
    "    c = ws.cell(row=1, column=col, value=h)\n"
    "    c.font = hdr_font; c.fill = hdr_fill\n"
    "    c.alignment = Alignment(horizontal='center'); c.border = border\n\n"
    "dados = [['A', 100], ['B', 200]]\n"
    "for row in dados: ws.append(row)\n"
    "for i in range(1, len(headers)+1):\n"
    "    ws.column_dimensions[get_column_letter(i)].width = 18\n"
    "for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(headers)):\n"
    "    for cell in row: cell.border = border\n\n"
    "wb.save(filepath)\n"
    "subprocess.Popen(f'start \"\" \"{filepath}\"', shell=True)\n"
    "print(f'Criado: {filepath}')\n\n"
    'FORMATO: {"steps":[{"step":1,"description":"...","code":"codigo completo"}]}'
)


class DataAgent:
    def __init__(self):
        self.model = "claude-haiku-4-5-20251001"
        self.name = "DATA"

    def plan(self, task, context=None):
        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)
        try:
            resp = client.messages.create(model=self.model, max_tokens=4000, system=PROMPT,
                messages=[{"role": "user", "content": "TAREFA: " + str(task) + ctx + "\nJSON puro."}])
            raw = resp.content[0].text.strip()
            plan = safe_parse(raw, self.model)
            steps = []
            for st in plan.get("steps", []):
                code = st.get("code", "").replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)
                steps.append({"step": st.get("step", 1), "description": st.get("description", ""),
                    "action": "run_python", "params": {"code": code, "description": st.get("description", "")}})
            return {"steps": steps, "agent": "DATA"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "DATA"}