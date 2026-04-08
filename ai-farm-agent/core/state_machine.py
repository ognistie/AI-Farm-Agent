"""
State Machine — Navegacao deterministica entre estados de aplicacoes.
Carrega mapas JSON e calcula o caminho do estado atual ao estado alvo.
"""

import json
import os
import time
from pathlib import Path


class StateMachine:
    def __init__(self, interaction_layer=None):
        self.il = interaction_layer
        self.maps = {}
        self._load_maps()

    def _load_maps(self):
        maps_dir = Path("state_maps")
        if maps_dir.exists():
            for f in maps_dir.glob("*.json"):
                try:
                    with open(f, encoding="utf-8") as fh:
                        data = json.load(fh)
                        if data and "app" in data:
                            self.maps[data["app"].lower()] = data
                except:
                    pass

    def identify_current_state(self, app_name):
        """Identifica em qual estado o app esta agora."""
        app_map = self._get_map(app_name)
        if not app_map:
            return "unknown"

        visible = set()
        if self.il:
            app_state = self.il.get_app_state(app_name)
            visible = set(t.lower() for t in app_state.get("visible_texts", []))

        best_match = "unknown"
        best_score = 0

        for state_name, state_data in app_map.get("states", {}).items():
            indicators = [i.lower() for i in
                state_data.get("indicators_uia", []) + state_data.get("indicators_ocr", [])]
            score = sum(1 for ind in indicators if any(ind in v for v in visible))
            if score > best_score:
                best_score = score
                best_match = state_name

        return best_match

    def navigate_to(self, app_name, target_state, params=None):
        """Navega do estado atual ate o estado alvo."""
        current = self.identify_current_state(app_name)
        app_map = self._get_map(app_name)

        if not app_map:
            return {"success": False, "error": f"Nenhum mapa para '{app_name}'"}

        if current == target_state:
            return {"success": True, "message": "Ja no estado correto"}

        current_data = app_map.get("states", {}).get(current, {})
        transitions = current_data.get("transitions", {})

        if target_state in transitions:
            steps = transitions[target_state]
            return self._execute_steps(app_name, steps, params or {})

        return {"success": False, "error": f"Sem caminho de '{current}' para '{target_state}'"}

    def get_workflow(self, app_name, workflow_name):
        """Retorna um workflow predefinido de um app."""
        app_map = self._get_map(app_name)
        if not app_map:
            return None
        return app_map.get("workflows", {}).get(workflow_name)

    def _execute_steps(self, app_name, steps, params):
        for step in steps:
            action = step.get("action", "")
            target = step.get("target", "")
            text = step.get("text", "")

            # Substitui variaveis
            for key, value in params.items():
                target = target.replace("{" + key + "}", str(value))
                text = text.replace("{" + key + "}", str(value))

            if action == "uia_click" and self.il:
                result = self.il.click_element(app_name, target)
            elif action == "uia_type" and self.il:
                result = self.il.type_in_field(app_name, target, text)
            elif action == "hotkey":
                import pyautogui
                keys = step.get("keys", "").split("+")
                pyautogui.hotkey(*keys)
                result = {"success": True}
            elif action == "wait_condition":
                from core.wait_engine import wait_for_condition
                result = wait_for_condition(step.get("condition", ""), target, timeout=10)
            else:
                result = {"success": False, "error": f"Acao desconhecida: {action}"}

            if not result.get("success"):
                return result
            time.sleep(0.3)

        return {"success": True}

    def _get_map(self, app_name):
        for key in self.maps:
            if app_name.lower() in key or key in app_name.lower():
                return self.maps[key]
        return None