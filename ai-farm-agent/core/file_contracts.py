"""Declarative FILE plans. No shell, Python or executable-open tool in this domain."""
import os
from pathlib import Path

FIELDS = {'open_path': ('path',), 'list_files': ('path',), 'find_files': ('path', 'pattern'), 'read_file': ('path',),
          'create_folder': ('path',), 'copy_file': ('source', 'destination'),
          'move_file': ('source', 'destination'), 'delete_file': ('path',)}


def request_roots(task):
    from agents.subagents import PathResolver
    from core.paths import extract_path
    roots = PathResolver().run(task).data['folders']
    explicit = extract_path(task)
    if explicit:
        roots.append(explicit)
    return sorted({os.path.realpath(p) for p in roots if p})


def validate(steps, roots, allow_delete=False):
    roots = [os.path.normcase(os.path.realpath(r)) for r in roots]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 40:
        return 'Plano FILE deve conter de 1 a 40 operacoes.'
    if not roots:
        return 'Informe a pasta ou caminho a operar; nao vou inferir um escopo.'
    for step in steps:
        if not isinstance(step, dict):
            return 'Operacao invalida.'
        action, params = step.get('action'), step.get('params')
        if action not in FIELDS or not isinstance(params, dict):
            return 'FILE aceita apenas ferramentas de arquivo declarativas.'
        if action == 'delete_file' and not allow_delete:
            return 'Exclusao requer confirmacao explicita no pedido original.'
        for key in FIELDS[action]:
            value = params.get(key)
            if not isinstance(value, str) or not value.strip():
                return f'Parametro obrigatorio: {key}.'
            if key == 'pattern':
                if '/' in value or '\\' in value or '..' in value:
                    return 'Pattern deve ser apenas um nome, sem caminho.'
                continue
            if not os.path.isabs(os.path.expanduser(os.path.expandvars(value))):
                return 'Caminhos devem ser absolutos.'
            path = os.path.normcase(os.path.realpath(os.path.expanduser(os.path.expandvars(value))))
            inside = False
            for root in roots:
                try:
                    inside = inside or os.path.commonpath([root, path]) == root
                except ValueError:
                    continue
            if not inside:
                return f'Caminho fora do escopo do pedido: {value}'
            if action in ('delete_file', 'move_file') and path in roots:
                return 'Operar a raiz inteira exige um procedimento separado; escolha arquivos internos.'
    return ''
