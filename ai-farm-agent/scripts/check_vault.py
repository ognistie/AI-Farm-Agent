"""Offline knowledge integrity: links, canonical procedures and retirement decisions."""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from core.brain import _frontmatter, _section
from core.vault_curation import load_retirements


def audit(vault):
    vault = Path(vault)
    # Runtime history is local, excluded from procedural retrieval and the default graph.
    files = [p for p in vault.rglob('*') if p.is_file() and p.suffix in ('.md', '.base', '.canvas')
             and not p.relative_to(vault).parts[0].startswith('.')]
    names, paths = defaultdict(list), set()
    for path in files:
        names[path.stem.casefold()].append(path)
        paths.add(path.relative_to(vault).as_posix().casefold())
    errors, canonical, guides = [], [], []
    for path in files:
        rel = path.relative_to(vault).as_posix()
        if path.suffix != '.md' or rel.startswith(('40 Execucoes/', '50 Diario/')):
            continue
        md = path.read_text(encoding='utf-8')
        fm = _frontmatter(md)
        text = re.sub(r'```.*?```', '', md, flags=re.S)
        for link in re.findall(r'\[\[([^\]]+)\]\]', text):
            target = link.split('|', 1)[0].split('#', 1)[0]
            if not target:
                continue
            if target.casefold() in paths or target.casefold() + '.md' in paths:
                continue
            matches = names.get(Path(target).stem.casefold(), [])
            if Path(target).suffix in ('.md', '.base', '.canvas'):
                matches = [candidate for candidate in matches if candidate.name.casefold() == Path(target).name.casefold()]
            else:
                matches = [candidate for candidate in matches if candidate.suffix == '.md']
            if len(matches) != 1:
                errors.append(f'{rel}: link ausente/ambiguo: {target}')
        if fm.get('tipo') == 'tarefa-referencia':
            canonical.append(rel)
            if not _section(md, 'Caminho') or not _section(md, 'Aceite e limites'):
                errors.append(rel + ': procedimento sem caminho ou aceite')
            if fm.get('verificado') not in ('sim', 'nao') or not fm.get('agente'):
                errors.append(rel + ': estado/agente ausente')
            if re.search(r'\brun_python\b|\brun_command\b|\bpip_install\b', _section(md, 'Caminho')):
                errors.append(rel + ': receita de execucao arbitraria aposentada')
        if fm.get('tipo') == 'playbook' and fm.get('estado') not in ('planejado', 'experimental', 'retirado'):
            guides.append(rel)
            if not _section(md, 'Caminho'):
                errors.append(rel + ': playbook ativo sem caminho')
    try:
        retired = len(load_retirements(vault))
    except (OSError, ValueError) as error:
        errors.append(str(error)); retired = 0
    return {'canonical_procedures': len(canonical), 'active_playbooks': len(guides),
            'retired_procedures': retired, 'errors': errors}


if __name__ == '__main__':
    result = audit(APP.parent / 'AI-Farm-agents')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['errors']))
