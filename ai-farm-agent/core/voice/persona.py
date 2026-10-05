"""
Persona do assistente — COMO ele fala (tom, regras e falas prontas).

Fonte: nota do Obsidian `00 Maestro/Persona do assistente.md` (o usuario
ajusta o jeito de falar sem mexer em codigo). Sem a nota, usa o padrao abaixo.

- style()               regras de fala para os prompts (entendimento, resposta final, resolvedor)
- pick(situacao, ...)   uma fala pronta, variando e sem repetir as recentes
                        ("Abrindo o Excel." / "Já abro o Excel." / "Excel chegando.")
Falas prontas existem para o que precisa ser INSTANTANEO (sem esperar o modelo).
"""

from __future__ import annotations

import random
import re
import threading
from pathlib import Path
from typing import Optional

NOTE = "00 Maestro/Persona do assistente.md"

STYLE = """- Você é um assistente pessoal no PC, no estilo de um mordomo digital competente: calmo, confiante, cordial e direto. Um toque leve de humor às vezes; nunca bajulador nem infantil.
- Português do Brasil de conversa ("tá", "pra", "já"), tratando o usuário por "você".
- Curto: confirmação em 2 a 8 palavras; resposta com dado = o dado primeiro, no máximo mais uma frase.
- Diga o que VAI fazer (gerúndio/futuro próximo) e só prometa o que vai mesmo acontecer. Nunca diga que fez algo que ainda não fez.
- Ações com consequência (enviar mensagem/e-mail, apagar, comprar, pagar, desligar): diga que vai preparar e confirmar antes — nunca "enviando" direto.
- Antecipe às vezes (não sempre) o próximo passo óbvio com uma pergunta curta ("Quer que eu toque o primeiro?").
- Varie o começo das frases; não repita as falas recentes. Evite abrir sempre com "Bora" ou "Beleza".
- Proibido: "Entendido", "Processando", "Certamente", "Como assistente", "Tarefa concluída", desculpas longas.
- Não leia URLs, caminhos de pasta, códigos ou ids."""

# situacao -> variacoes. {obj}, {q}, {cmd}, {where}, {msg}, {guess} sao preenchidos na hora.
LINES = {
    "listening_on": ["Tô ouvindo. Pode falar.", "Pode mandar, tô aqui.", "Ouvindo. Manda.", "Pronto, pode falar."],
    "listening_off": ["Beleza, parei de ouvir.", "Microfone desligado.", "Fechado, saí da escuta."],
    "ack": ["Beleza.", "Feito.", "Certo.", "Pode deixar.", "Fechado."],
    "retry": ["Tá, fala de novo do seu jeito.", "Sem problema, me diz de novo.", "Ok, repete pra mim?"],
    "not_heard": ["Não peguei. Pode repetir?", "Escapou aqui. Fala de novo?", "Não ouvi direito. Repete?"],
    "confirm_guess": ["Foi pra {guess}?", "Você quis dizer {guess}?", "Seria {guess}?"],
    "what_open": ["Abrir o quê?", "Abro qual?", "Qual app ou site?"],
    "queued": ["Anotado: depois disso, {cmd}.", "Fica na fila: {cmd}.", "Já já: {cmd}, assim que terminar."],
    "stopped": ["Parei.", "Parado.", "Ok, interrompi."],
    "working": ["Ainda tô nisso{where}, quase lá.", "Tá levando um pouquinho{where}, sigo aqui.",
                "Continuo trabalhando{where}."],
    "failed": ["Não deu certo: {msg}", "Travei aqui: {msg}", "Não consegui: {msg}"],
    "start_fail": ["Não consegui começar esse pedido. Pode repetir?", "Esse não começou. Manda de novo?"],
    "mic_error": ["Não consegui usar o microfone.", "O microfone não respondeu."],
    "stt_error": ["O reconhecimento de voz não carregou.", "Minha audição não carregou ainda."],
    "open": ["Abrindo {obj}.", "Já abro {obj}.", "{Obj} chegando.", "Um segundo, {obj} na tela.", "Abrindo {obj} pra você."],
    "search": ["Pesquisando {q}.", "Procurando {q}.", "Deixa comigo: {q}.", "Buscando {q}."],
    "thanks": ["Imagina! Se precisar, é só chamar.", "Tamo junto. Tô por aqui.", "De nada. Qualquer coisa, me chama.",
               "Disponha. Quando quiser continuar, é só pedir."],
    "hello": ["Oi! O que vamos fazer agora?", "E aí! No que eu te ajudo?", "Opa, tô aqui. Manda o pedido."],
    "time": ["São {msg}.", "Agora são {msg}.", "{Msg} agora."],
    "date": ["Hoje é {msg}.", "É {msg}."],
}


def _parse_note(md: str) -> tuple[str, dict]:
    style_lines, lines = [], {}
    sec = ""
    for raw in md.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            sec = re.sub(r"[^a-z ]", "", line[3:].lower()).strip()
            continue
        if sec.startswith("estilo") and line.startswith("- "):
            style_lines.append(line)
        elif sec.startswith("falas") and line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3 and cells[0].lower() not in ("chave", "situação", "situacao"):
                key = cells[0].strip("` ")
                options = [o.strip() for o in cells[2].split(" / ") if o.strip()]
                if key and options:
                    lines[key] = options
    return "\n".join(style_lines), lines


class Persona:
    def __init__(self, vault: Optional[Path] = None):
        self._vault = vault
        self._stamp = None
        self._style = STYLE
        self._lines = dict(LINES)
        self._lock = threading.Lock()
        self.recent: list[str] = []

    def _path(self) -> Optional[Path]:
        try:
            if self._vault is None:
                from core.brain import get_brain
                self._vault = get_brain().root
            return Path(self._vault) / NOTE
        except Exception:
            return None

    def _load(self) -> None:
        p = self._path()
        try:
            stamp = p.stat().st_mtime if p else None
        except OSError:
            stamp = None
        if stamp == self._stamp:
            return
        self._stamp = stamp
        style, lines = ("", {})
        if stamp is not None:
            try:
                style, lines = _parse_note(p.read_text(encoding="utf-8"))
            except OSError:
                pass
        self._style = style or STYLE
        merged = dict(LINES)
        # so aceita variacoes que usam os mesmos campos da padrao (fala quebrada nunca vai pro ar)
        for k, opts in lines.items():
            want = set(re.findall(r"{(\w+)}", " ".join(LINES.get(k, [])).lower()))
            ok = [o for o in opts if set(re.findall(r"{(\w+)}", o.lower())) <= want]
            if ok:
                merged[k] = ok
        self._lines = merged

    def style(self) -> str:
        with self._lock:
            self._load()
            return self._style

    def pick(self, situation: str, recent: Optional[list] = None, **fields) -> str:
        with self._lock:
            self._load()
            options = list(self._lines.get(situation) or [])
        if not options:
            return ""
        avoid = set((recent if recent is not None else self.recent)[-4:])
        filled = [_fill(o, fields) for o in options]
        fresh = [f for f in filled if f not in avoid] or filled
        out = random.choice(fresh)
        self.recent = (self.recent + [out])[-8:]
        return out


def _fill(template: str, fields: dict) -> str:
    def rep(m):
        key = m.group(1)
        val = str(fields.get(key.lower(), "") or "")
        return val[:1].upper() + val[1:] if key[:1].isupper() else val
    out = re.sub(r"{(\w+)}", rep, template)
    return re.sub(r"\s+([.,!?])", r"\1", re.sub(r"\s{2,}", " ", out)).strip()


_instance: Optional[Persona] = None


def get_persona() -> Persona:
    global _instance
    if _instance is None:
        _instance = Persona()
    return _instance
