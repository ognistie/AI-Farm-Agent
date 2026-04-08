"""
FileAgent v11 — Upgrade do v9.
MUDANCAS: Fix f-string braces, exemplos no prompt.
"""

import json, os, getpass
from anthropic import Anthropic
from core.json_validator import safe_parse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
USERNAME = getpass.getuser()
BASE = "C:/Users/" + USERNAME

PROMPT = (
    "Voce e o FILE AGENT — sysadmin senior em arquivos Windows.\n"
    "Downloads: " + BASE + "/Downloads. Desktop: " + BASE + "/Desktop.\n\n"
    "REGRAS:\n"
    "1. SEMPRE: import os, shutil, glob, pathlib, subprocess\n"
    "2. SEMPRE: caminho absoluto\n"
    "3. SEMPRE: print() detalhado\n"
    "4. SEMPRE: abre Explorer no final: subprocess.Popen(['explorer', pasta])\n"
    "5. NUNCA delete sem confirmacao\n"
    "6. UMA step com codigo completo\n\n"
    "EXEMPLO — Organizar Downloads por tipo:\n"
    "import os, shutil, subprocess\n"
    "downloads = os.path.join(os.path.expanduser('~'), 'Downloads')\n"
    "tipos = {'Imagens':['.jpg','.png','.gif'], 'Docs':['.pdf','.docx','.xlsx'], 'Videos':['.mp4','.avi']}\n"
    "moved = 0\n"
    "for f in os.listdir(downloads):\n"
    "    fp = os.path.join(downloads, f)\n"
    "    if not os.path.isfile(fp): continue\n"
    "    ext = os.path.splitext(f)[1].lower()\n"
    "    for pasta, exts in tipos.items():\n"
    "        if ext in exts:\n"
    "            dest = os.path.join(downloads, pasta)\n"
    "            os.makedirs(dest, exist_ok=True)\n"
    "            shutil.move(fp, os.path.join(dest, f))\n"
    "            moved += 1; break\n"
    "subprocess.Popen(['explorer', downloads])\n"
    "print(f'{moved} arquivos organizados')\n\n"
    '{"steps":[{"step":1,"description":"...","code":"codigo python"}]}'
)


class FileAgent:
    def __init__(self):
        self.model = "claude-haiku-4-5-20251001"
        self.name = "FILE"

    def plan(self, task, context=None):
        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)
        try:
            resp = client.messages.create(model=self.model, max_tokens=3000, system=PROMPT,
                messages=[{"role": "user", "content": "TAREFA: " + str(task) + ctx + "\nJSON puro."}])
            raw = resp.content[0].text.strip()
            plan = safe_parse(raw, self.model)
            steps = []
            for st in plan.get("steps", []):
                code = st.get("code", "").replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)
                steps.append({"step": st.get("step", 1), "description": st.get("description", ""),
                    "action": "run_python", "params": {"code": code, "description": st.get("description", "")}})
            return {"steps": steps, "agent": "FILE"}
        except Exception as ex:
            return {"steps": [], "error": str(ex), "agent": "FILE"}