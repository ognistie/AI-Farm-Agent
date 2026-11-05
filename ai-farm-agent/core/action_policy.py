"""Execution-time domain authorization. Model-generated steps cannot choose their owner."""
from core.file_contracts import FIELDS, request_roots, validate

TOOLS = {
    'CODE': {'create_project', 'edit_project', 'revert_project', 'wait'},
    'DATA': {'create_workbook', 'wait'},
    'FILE': set(FIELDS) | {'wait'},
    'WEB': {'open_url', 'browser_task', 'browser_click', 'browser_read', 'web_goto', 'web_new_tab',
            'web_click', 'web_type', 'web_key', 'web_read', 'wait', 'wait_for_window', 'focus_window'},
    'DESKTOP': {'app_search', 'open_app', 'app_type', 'blank_document', 'app_task', 'open_path',
                'close_app', 'focus_window', 'type_text', 'hotkey', 'click', 'vision_click',
                'vision_type', 'vision_analyze', 'vision_verify', 'vision_smart', 'uia_click',
                'uia_type', 'wait', 'wait_for_window', 'wait_for_element', 'screenshot'},
}


def authorize(agent, task, action, params):
    if action not in TOOLS.get(agent, set()):
        return f'Ferramenta {action} nao autorizada para {agent or "contexto ausente"}.'
    if agent == 'FILE' and action != 'wait':
        from agents.file_agent import _has_explicit_confirmation
        return validate([{'action': action, 'params': params}], request_roots(task), _has_explicit_confirmation(task))
    return ''
