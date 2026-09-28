"""
VisionMaestro v9 — Supervisor visual. Verifica ANTES e DEPOIS de cada ação.
Detecta anomalias, janelas erradas, popups bloqueantes.
"""

import json, os, time
from core.ai_client import get_client
from core.config import get_config

SYS = """Você é o SUPERVISOR VISUAL de um sistema de automação Windows PT-BR.
Você vê screenshots reais e analisa o estado da tela com precisão cirúrgica.

O que observar:
1. Janela em foco (barra de título destacada = foco)
2. Estado do app (carregando? dialog aberto? erro?)
3. Alertas/popups bloqueantes
4. Se o browser do AI Farm Agent (127.0.0.1) está na frente

Sinais de problema:
- Janela cinza/travada → app não responde
- Dialog de erro → precisa fechar
- Loading/spinner → precisa esperar
- Browser na frente → precisa minimizar
- Tela preta/desktop → app fechou

JSON puro, sem markdown."""


class VisionMaestro:
    def __init__(self, vision_engine):
        self.vision = vision_engine
        self.model = get_config().get_model("vision_maestro")
        self.effort = get_config().get_effort("vision_maestro")
        self.enabled = True

    def check_before(self, action, params, description):
        """Verifica se a tela está pronta ANTES da ação."""
        if not self.enabled or not self.vision:
            return {"safe": True}

        # Ações que não precisam de check visual
        skip = {"run_python","run_command","write_file","create_folder","read_file",
                "list_files","move_file","copy_file","delete_file","find_files",
                "pip_install","wait","excel_write","web_goto","web_type","web_click",
                "web_key","web_read","web_new_tab","hotkey"}
        if action in skip:
            return {"safe": True}

        try:
            b64, img, r = self.vision.take_screenshot()
            prompt = f"""O agente quer executar: {action}
Params: {json.dumps(params, ensure_ascii=False)[:200]}
Descrição: {description}

A tela está pronta?
JSON: {{"safe":true/false,"current_state":"...","correction":"se necessário","correction_steps":[{{"action":"...","params":{{}}}}]}}"""

            raw = get_client().message(model=self.model, system=SYS,
                user_content=prompt, images=[{"base64": b64}], max_tokens=3000,
                effort=self.effort, agent="VISION_MAESTRO")
            if raw.startswith("```"): raw = raw.split("\n",1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"): raw = raw[:-3]
            result = json.loads(raw.strip())
            if not result.get("safe", True):
                print(f"  🔍 [PRÉ] {result.get('correction','Correção necessária')}")
            return result
        except Exception as e:
            # Falha do check NUNCA bloqueia a acao (degrada para "safe"),
            # mas registra a causa para diagnostico futuro.
            print(f"  [VisionMaestro] check_before falhou: {e}")
            return {"safe": True, "check_failed": True, "error": str(e)}

    def check_after(self, action, description):
        """Verifica se a ação teve sucesso DEPOIS da execução."""
        if not self.enabled or not self.vision:
            return {"valid": True}

        skip = {"run_python","run_command","write_file","wait","excel_write",
                "web_goto","web_type","web_click","web_key","pip_install",
                "create_folder","read_file","list_files","hotkey"}
        if action in skip:
            return {"valid": True}

        try:
            time.sleep(0.5)  # espera UI atualizar
            b64, _, _ = self.vision.take_screenshot()
            prompt = f"""A ação '{action}' foi executada: {description}
Funcionou? A tela confirma o resultado esperado?
JSON: {{"valid":true/false,"actual_state":"o que vejo na tela","issue":"se falhou, qual o problema"}}"""

            raw = get_client().message(model=self.model, system=SYS,
                user_content=prompt, images=[{"base64": b64}], max_tokens=3000,
                effort=self.effort, agent="VISION_MAESTRO")
            if raw.startswith("```"): raw = raw.split("\n",1)[1]
            if raw.endswith("```"): raw = raw[:-3]
            result = json.loads(raw.strip())
            if not result.get("valid", True):
                print(f"  🔍 [PÓS] Falhou: {result.get('issue','')}")
            return result
        except Exception as e:
            print(f"  [VisionMaestro] check_after falhou: {e}")
            return {"valid": True, "check_failed": True, "error": str(e)}