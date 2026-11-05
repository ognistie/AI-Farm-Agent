"""Explicit, reviewable retirement decisions; prevents legacy archives undoing curation."""
import json
from pathlib import Path


def load_retirements(vault):
    vault = Path(vault).resolve()
    path = vault.parent / 'docs' / 'research' / 'vault-curation.json'
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('retired'), list):
        raise ValueError('Manifesto de curadoria invalido.')
    entries = {}
    prefix = vault.name + '/30 Tarefas de referencia/'
    for item in data['retired']:
        if not isinstance(item, dict):
            raise ValueError('Decisao de curadoria invalida.')
        key, target = item.get('path'), item.get('replacement')
        if (not isinstance(key, str) or not key.startswith(prefix) or '\\' in key
                or '..' in key.split('/') or key in entries
                or item.get('decision') != 'consolidated'
                or not isinstance(item.get('reason'), str) or len(item['reason'].strip()) < 20
                or not isinstance(target, str) or not target.startswith(vault.name + '/')
                or not isinstance(item.get('source_sha256'), str) or len(item['source_sha256']) != 64):
            raise ValueError('Decisao incompleta, duplicada ou fora do escopo.')
        resolved = (vault.parent / target).resolve()
        if not resolved.is_relative_to(vault) or not resolved.is_file():
            raise ValueError('Substituto da nota retirada esta ausente ou fora do vault: ' + key)
        if (vault.parent / key).exists():
            raise ValueError('Nota retirada reapareceu no vault: ' + key)
        entries[key] = item
    return entries


def retired_reference_paths(vault):
    vault = Path(vault)
    prefix = vault.name + '/30 Tarefas de referencia/'
    return {path.removeprefix(prefix) for path in load_retirements(vault)}


def review_deletions(vault, deleted_hashes):
    """Accept only named deletions whose baseline content matches the reviewed source."""
    entries = load_retirements(vault)
    reviewed, pending = [], []
    for path, digest in deleted_hashes.items():
        item = entries.get(path)
        (reviewed if item and item['source_sha256'] == digest else pending).append(path)
    return {'reviewed': reviewed, 'pending': pending}
