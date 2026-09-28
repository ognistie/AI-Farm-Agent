"""
JSON Validator — Auto-repara JSON mal-formado dos agentes.
Fix: lida com "Extra data" (dois JSONs na resposta).
"""

import json, re

REPAIR_MAX_CHARS = 6000


def safe_parse(raw, model=None):
    """Parseia JSON com multiplas tentativas de reparo."""

    # 1. Limpa markdown
    clean = re.sub(r'```json|```', '', raw).strip()

    # 2. Tenta direto
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # 3. Extrai PRIMEIRO bloco JSON completo (resolve "Extra data")
    first_json = _extract_first_json(clean)
    if first_json:
        try:
            return json.loads(first_json)
        except:
            pass

    # 4. Tenta do primeiro { ao ultimo }
    s, e = clean.find('{'), clean.rfind('}')
    if s != -1 and e != -1:
        block = clean[s:e+1]
        try:
            return json.loads(block)
        except:
            pass

        # 5. Repara erros comuns
        fixed = block
        fixed = re.sub(r'\}\s*\{', '}, {', fixed)
        fixed = re.sub(r'\]\s*\{', '], {', fixed)
        fixed = re.sub(r',\s*\}', '}', fixed)
        fixed = re.sub(r',\s*\]', ']', fixed)
        fixed = fixed.replace("'", '"')
        try:
            return json.loads(fixed)
        except:
            pass

    # 6. Pede correcao ao modelo — so para respostas curtas. Uma resposta
    # longa (codigo gerado) cortada ao meio nao tem conserto: e mais barato
    # o agente refazer a chamada do que pagar um reparo que devolve lixo.
    try:
        if len(clean) > REPAIR_MAX_CHARS:
            raise ValueError("resposta longa demais para reparo via LLM")
        from core.ai_client import get_client
        from core.config import get_config
        cfg = get_config()
        corrected = get_client().message(
            model=model or cfg.get("models.fast"), system="",
            user_content="Corrija este JSON invalido. Retorne APENAS o JSON corrigido:\n\n" + clean,
            max_tokens=8000, effort=cfg.get_effort("json_repair"), agent="JSON_REPAIR")
        corrected = re.sub(r'```json|```', '', corrected).strip()
        first = _extract_first_json(corrected)
        if first:
            return json.loads(first)
        s2, e2 = corrected.find('{'), corrected.rfind('}')
        if s2 != -1 and e2 != -1:
            return json.loads(corrected[s2:e2+1])
    except:
        pass

    # 7. Regex de ultimo recurso
    steps = []
    for m in re.finditer(r'\{"step"\s*:\s*(\d+).*?"action"\s*:\s*"([^"]+)".*?"description"\s*:\s*"([^"]+)"', clean, re.DOTALL):
        steps.append({"step": int(m.group(1)), "action": m.group(2), "description": m.group(3), "params": {}})
    if steps:
        return {"steps": steps}

    # 8. Tenta extrair subtasks
    st_match = re.search(r'"subtasks"\s*:\s*\[.*?\]', clean, re.DOTALL)
    if st_match:
        try:
            return json.loads('{' + st_match.group(0) + '}')
        except:
            pass

    raise ValueError("JSON irrecuperavel: " + clean[:200])


def _extract_first_json(text):
    """Extrai o PRIMEIRO objeto JSON completo do texto."""
    depth = 0
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                return text[start:i+1]
    return None