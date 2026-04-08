"""
Interaction Layer — Camada de abstracao de interacao.
Tenta a estrategia mais confiavel primeiro, faz fallback automatico.
Nivel 1: API/Codigo → Nivel 2: UIA → Nivel 3: Vision
"""

from core.uia_driver import UIADriver
import logging

logger = logging.getLogger("interaction_layer")


class InteractionLayer:
    def __init__(self, vision_engine=None):
        self.uia = UIADriver()
        self.vision = vision_engine

    def click_element(self, app_name, element_desc):
        """Clica em um elemento usando a melhor estrategia."""
        # NIVEL 2: UIA
        result = self.uia.try_click(app_name, element_desc)
        if result.get("success"):
            logger.info(f"UIA click OK: {element_desc}")
            return {"success": True, "method": "UIA", "details": result}

        # NIVEL 3: Vision
        if self.vision:
            logger.info(f"UIA falhou, tentando Vision: {element_desc}")
            r = self.vision.find_element(element_desc)
            if r.get("found"):
                x, y = r.get("x", 0), r.get("y", 0)
                import pyautogui
                sw, sh = pyautogui.size()
                if y < sh - 60:  # Protecao taskbar
                    from core.automation import human_move
                    human_move(x, y)
                    import time; time.sleep(0.15)
                    pyautogui.click()
                    return {"success": True, "method": "VISION", "x": x, "y": y}
            return {"success": False, "method": "VISION", "error": r.get("reason", "Nao encontrado")}

        return {"success": False, "error": "UIA falhou e Vision nao disponivel"}

    def type_in_field(self, app_name, field_desc, text):
        """Digita em um campo usando a melhor estrategia."""
        # NIVEL 2: UIA
        result = self.uia.try_type(app_name, field_desc, text)
        if result.get("success"):
            logger.info(f"UIA type OK: {field_desc}")
            return {"success": True, "method": "UIA"}

        # NIVEL 3: Vision
        if self.vision:
            logger.info(f"UIA falhou, tentando Vision type: {field_desc}")
            r = self.vision.find_element(field_desc)
            if r.get("found"):
                x, y = r.get("x", 0), r.get("y", 0)
                import pyautogui
                sw, sh = pyautogui.size()
                if y < sh - 60:
                    from core.automation import human_move
                    human_move(x, y)
                    import time
                    time.sleep(0.15)
                    pyautogui.click()
                    time.sleep(0.2)
                    pyautogui.click()
                    time.sleep(0.3)
                    try:
                        import pyperclip
                        pyperclip.copy(text)
                        pyautogui.hotkey("ctrl", "v")
                    except:
                        pyautogui.write(text)
                    return {"success": True, "method": "VISION", "x": x, "y": y}
            return {"success": False, "method": "VISION", "error": "Campo nao encontrado"}

        return {"success": False, "error": "UIA falhou e Vision nao disponivel"}

    def get_app_state(self, app_name):
        """Identifica o estado atual de um app."""
        # UIA
        state = self.uia.read_app_state(app_name)
        if state.get("identified"):
            return state

        # Fallback: OCR local
        try:
            from core.ocr_local import read_screen_text
            texts = read_screen_text()
            return {"identified": True, "method": "OCR", "visible_texts": [t["text"] for t in texts]}
        except:
            return {"identified": False}