"""
UIA Driver — Acessa a arvore de acessibilidade do Windows via pywinauto.
Permite interagir com apps por nome/tipo de controle, nao por pixel.
"""

import logging
import time

logger = logging.getLogger("uia_driver")

# Mapa de controles conhecidos por app
CONTROL_MAPS = {
    "teams": {
        "chat": {"title": "Chat", "control_type": "TreeItem", "alt_titles": ["Chat", "Bate-papo"]},
        "activity": {"title": "Activity", "control_type": "TreeItem", "alt_titles": ["Atividade"]},
        "search": {"title": "Search", "control_type": "Edit", "alt_titles": ["Pesquisar"]},
        "message_box": {"title": "Type a new message", "control_type": "Edit", "alt_titles": ["Digite uma nova mensagem", "Digite uma mensagem"]},
        "send": {"title": "Send", "control_type": "Button", "alt_titles": ["Enviar"]},
    },
    "excel": {
        "name_box": {"title": "Name Box", "control_type": "Edit"},
        "formula_bar": {"title": "Formula Bar", "control_type": "Edit"},
    },
    "vscode": {
        "command_palette": {"hotkey": ["ctrl", "shift", "p"]},
        "terminal": {"hotkey": ["ctrl", "`"]},
        "explorer": {"hotkey": ["ctrl", "shift", "e"]},
        "new_file": {"hotkey": ["ctrl", "n"]},
    },
    "notepad": {
        "text_area": {"title": "", "control_type": "Edit"},
    },
    "word": {
        "blank_doc": {"title": "Blank document", "control_type": "Button", "alt_titles": ["Documento em branco"]},
    },
}


class UIADriver:
    def connect_app(self, app_name):
        """Conecta a um app pelo titulo da janela."""
        try:
            from pywinauto import Application
            app = Application(backend="uia").connect(title_re=f".*{app_name}.*", timeout=5)
            return {"success": True, "app": app}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def try_click(self, app_name, element_desc):
        """Tenta clicar em um elemento via UIA."""
        conn = self.connect_app(app_name)
        if not conn["success"]:
            return conn

        app = conn["app"]
        try:
            window = app.top_window()
            window.set_focus()
            time.sleep(0.3)

            # Tenta pelo mapa de controles conhecidos
            app_key = app_name.lower()
            for map_key in CONTROL_MAPS:
                if map_key in app_key or app_key in map_key:
                    controls = CONTROL_MAPS[map_key]
                    for ctrl_name, ctrl_info in controls.items():
                        if element_desc.lower() in ctrl_name or ctrl_name in element_desc.lower():
                            # Hotkey
                            if "hotkey" in ctrl_info:
                                import pyautogui
                                pyautogui.hotkey(*ctrl_info["hotkey"])
                                return {"success": True, "method": "hotkey"}

                            # UIA click com titulos alternativos
                            titles = [ctrl_info["title"]] + ctrl_info.get("alt_titles", [])
                            ctrl_type = ctrl_info.get("control_type", "")
                            for title in titles:
                                try:
                                    if ctrl_type:
                                        el = window.child_window(title_re=f".*{title}.*", control_type=ctrl_type, found_index=0)
                                    else:
                                        el = window.child_window(title_re=f".*{title}.*", found_index=0)
                                    if el.exists(timeout=2):
                                        el.click_input()
                                        return {"success": True, "method": "control_map", "title": title}
                                except:
                                    continue

            # Busca generica por texto
            try:
                el = window.child_window(title_re=f".*{element_desc}.*", found_index=0)
                if el.exists(timeout=3):
                    el.click_input()
                    return {"success": True, "method": "generic_search"}
            except:
                pass

            return {"success": False, "error": f"Elemento '{element_desc}' nao encontrado via UIA"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def try_type(self, app_name, field_desc, text):
        """Tenta digitar em um campo via UIA."""
        conn = self.connect_app(app_name)
        if not conn["success"]:
            return conn

        try:
            window = conn["app"].top_window()
            window.set_focus()
            time.sleep(0.3)

            # Busca campo de texto
            app_key = app_name.lower()
            for map_key in CONTROL_MAPS:
                if map_key in app_key or app_key in map_key:
                    controls = CONTROL_MAPS[map_key]
                    for ctrl_name, ctrl_info in controls.items():
                        if field_desc.lower() in ctrl_name or ctrl_name in field_desc.lower():
                            titles = [ctrl_info.get("title", "")] + ctrl_info.get("alt_titles", [])
                            for title in titles:
                                try:
                                    el = window.child_window(title_re=f".*{title}.*", control_type="Edit", found_index=0)
                                    if el.exists(timeout=2):
                                        el.set_focus()
                                        el.type_keys(text, with_spaces=True, with_newlines=True)
                                        return {"success": True, "method": "control_map"}
                                except:
                                    continue

            # Busca generica
            try:
                el = window.child_window(title_re=f".*{field_desc}.*", control_type="Edit", found_index=0)
                if el.exists(timeout=3):
                    el.set_focus()
                    el.type_keys(text, with_spaces=True, with_newlines=True)
                    return {"success": True, "method": "generic"}
            except:
                pass

            return {"success": False, "error": f"Campo '{field_desc}' nao encontrado via UIA"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_app_state(self, app_name):
        """Le o estado atual de um app via UIA."""
        conn = self.connect_app(app_name)
        if not conn["success"]:
            return {"identified": False}

        try:
            window = conn["app"].top_window()
            title = window.window_text()
            visible = []
            for ctrl in window.descendants():
                try:
                    t = ctrl.window_text()
                    if t and len(t) < 200:
                        visible.append(t)
                except:
                    pass
            return {"identified": True, "method": "UIA", "window_title": title, "visible_texts": visible[:50]}
        except Exception as e:
            return {"identified": False, "error": str(e)}

    def list_controls(self, app_name):
        """Debug: lista todos os controles de um app."""
        conn = self.connect_app(app_name)
        if not conn["success"]:
            return conn["error"]
        window = conn["app"].top_window()
        window.print_control_identifiers()
        return "Controles impressos no console."