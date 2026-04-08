"""
Wait Engine v2 — Esperas condicionais com busca flexivel de janela.
Busca por titulo parcial usando pygetwindow (mais confiavel que pywinauto para detecao).
"""

import time


def wait_for_window(title, timeout=15):
    """Espera ate que uma janela com o titulo apareca. Busca parcial."""
    start = time.time()
    search = title.lower()
    while time.time() - start < timeout:
        try:
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if w.visible and w.title and search in w.title.lower():
                    return {"success": True, "window_title": w.title, "elapsed": round(time.time() - start, 1)}
        except:
            pass
        time.sleep(0.5)

    # Fallback: tenta pywinauto
    try:
        from pywinauto import Application
        app = Application(backend="uia").connect(title_re=".*" + title + ".*", timeout=3)
        return {"success": True, "elapsed": round(time.time() - start, 1)}
    except:
        pass

    return {"success": False, "error": "Timeout: '" + title + "' nao apareceu em " + str(timeout) + "s"}


def wait_for_element(app_name, element_title, timeout=10):
    """Espera ate que um elemento apareca numa janela."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            from pywinauto import Application
            app = Application(backend="uia").connect(title_re=".*" + app_name + ".*", timeout=1)
            window = app.top_window()
            el = window.child_window(title_re=".*" + element_title + ".*", found_index=0)
            if el.exists():
                return {"success": True, "elapsed": round(time.time() - start, 1)}
        except:
            pass
        time.sleep(0.5)
    return {"success": False, "error": "Timeout: '" + element_title + "' nao encontrado em " + str(timeout) + "s"}


def wait_for_condition(condition, target, timeout=10):
    if condition == "window_exists":
        return wait_for_window(target, timeout)
    elif condition == "element_visible":
        parts = target.split("::") if "::" in target else ["", target]
        return wait_for_element(parts[0], parts[-1], timeout)
    else:
        time.sleep(min(timeout, 3))
        return {"success": True, "method": "fixed_wait"}