"""
ReportNarrator v6 — Usa safe_parse em vez de json.loads. Haiku em vez de Sonnet.
"""

import json, os, base64
from datetime import datetime
from anthropic import Anthropic
from core.json_validator import safe_parse

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYS = "Gere relatorio skill-builder. JSON puro, sem markdown.\nPara cada passo: {\"what\":\"1 frase\",\"concept\":\"tag\",\"insight\":\"1 frase\"}\nGeral: {\"summary\":\"1-2 frases\",\"skills\":[\"tags\"],\"xp_earned\":50-500,\"next_level\":\"1 frase\"}"

class ReportNarrator:
    def __init__(self, reports_dir="reports"):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        self.model = "claude-haiku-4-5-20251001"  # Haiku (era Sonnet, economia 12x)

    def generate_report(self, task, records, captures_b64=None):
        logs = "\n".join(
            str(i+1) + ". " + ("OK" if r.get("success") else "FAIL") + " [" + r.get("action","") + "] " + str(r.get("result",""))[:80]
            for i, r in enumerate(records)
        )
        content = []
        if captures_b64:
            for c in captures_b64[:2]:  # Max 2 screenshots (economia)
                content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": c["base64"]}})
                content.append({"type": "text", "text": "[Passo " + str(c["step"]) + "]"})
        content.append({"type": "text", "text": "TAREFA: " + task + "\nLOGS:\n" + logs + "\n\nJSON puro."})
        try:
            resp = client.messages.create(model=self.model, max_tokens=1500, system=SYS,
                messages=[{"role": "user", "content": content}])
            raw = resp.content[0].text.strip()
            # Usa safe_parse em vez de json.loads (lida com JSON mal-formado)
            report = safe_parse(raw, self.model)
            report["task"] = task
            report["generated_at"] = datetime.now().isoformat()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.reports_dir, "report_" + ts + ".json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            return report
        except Exception as e:
            return {"error": True, "message": str(e), "task": task}