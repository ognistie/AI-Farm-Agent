"""
FileAgent v12 — Migrado para BaseAgent.
Especialista em organização de arquivos. Usa os/shutil/glob.
"""

import json
import os
import getpass
from agents.base_agent import BaseAgent

USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"

SYSTEM_PROMPT = (
    "Voce e o FILE AGENT — sysadmin senior em arquivos Windows.\n"
    "Use os.path.expanduser('~') para obter o diretorio do usuario.\n"
    "Downloads: expanduser + /Downloads. Desktop: expanduser + /Desktop.\n\n"
    "REGRAS:\n"
    "1. SEMPRE: import os, shutil, glob, pathlib, subprocess\n"
    "2. SEMPRE: caminho absoluto usando os.path.expanduser('~')\n"
    "3. SEMPRE: print() detalhado (origem, destino, contagem)\n"
    "4. SEMPRE: abre Explorer no final: subprocess.Popen(['explorer', pasta])\n"
    "5. UMA step com codigo completo\n\n"
    "PRINCIPIOS OPERACIONAIS (BRIEFING):\n"
    "- Verificar antes de destrutivo: ANTES de delete/move/rmtree, use\n"
    "  os.path.exists + print do que sera afetado. Em duvida, send to .Trash.\n"
    "- Colisao de nomes (cenario D): NUNCA sobrescrever. Renomeie destino com\n"
    "  sufixo _2/_3 e logue. Para overwrites, exija flag CONFIRM_OVERWRITE=True.\n"
    "- Recursos (cenario I): operacoes em massa (>500MB) → checar shutil.disk_usage\n"
    "  antes. Abortar com print claro se livre < 2x do necessario.\n"
    "- Falha rapida: try/except deve PRINTAR a excecao literal antes de re-raise.\n"
    "  Nunca workaround silencioso.\n"
    "- Idempotencia: o mesmo prompt rodado 2x nao pode duplicar acoes nem perder\n"
    "  arquivos. Use os.path.exists antes de criar/mover.\n\n"
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


class FileAgent(BaseAgent):
    """Agente especialista em gerenciamento de arquivos."""

    def __init__(self):
        super().__init__(name="FILE", system_prompt=SYSTEM_PROMPT)

    def plan(self, task, context=None):
        """Gera plano e converte steps de code para run_python."""
        task_text = self._extract_task_text(task)

        ctx = ""
        if context:
            ctx = "\nCONTEXTO: " + json.dumps(context)

        try:
            raw = self._client.message(
                model=self.model,
                system=self.system_prompt,
                user_content=f"TAREFA: {task_text}{ctx}\nJSON puro.",
                max_tokens=3000,
            )
            from core.json_validator import safe_parse
            plan = safe_parse(raw, self.model)

            steps = []
            for st in plan.get("steps", []):
                code = st.get("code", "")
                code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)
                steps.append({
                    "step": st.get("step", 1),
                    "description": st.get("description", ""),
                    "action": "run_python",
                    "params": {"code": code, "description": st.get("description", "")},
                    "agent": "FILE",
                })

            self.logger.info(f"Plano: {len(steps)} steps")
            self._metrics["total_plans"] += 1
            self._metrics["successful_plans"] += 1
            return {"steps": steps, "agent": "FILE"}

        except Exception as e:
            self.logger.error(f"Erro: {e}")
            self._metrics["total_plans"] += 1
            self._metrics["failed_plans"] += 1
            return {"steps": [], "error": str(e), "agent": "FILE"}