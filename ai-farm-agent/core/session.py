"""
Session — a conversa continua entre pedidos.

Antes cada pedido era uma execucao isolada: "agora abra esse segundo video"
chegava sem saber que "esse" era a lista do YouTube aberta no pedido
anterior. A sessao guarda, entre pedidos:

- turns:   o que foi dito, como foi entendido e o resultado (resumido)
- estado do mundo: o que ficou aberto e onde
    web     aba do navegador usada (janela, URL, titulo, itens visiveis)
    apps    janelas de app por chave (notepad, spotify...)
    code    pasta do ultimo projeto e seus arquivos
    folder  ultima pasta/arquivo de FILE
- focus:   qual desses e o "atual" (o alvo de "esse", "agora", "aquele")
- pending: pergunta de esclarecimento aguardando resposta

O estado serve para RESOLVER referencias. Antes de agir, o agente sempre
olha a tela de novo: o usuario pode ter mexido no PC entre um pedido e outro.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

MAX_TURNS = 200          # conversa inteira (o contexto do modelo usa so as ultimas)
SESSIONS_DIR = Path(__file__).resolve().parent.parent / "memory" / "sessions"


def _alive(hwnd) -> bool:
    """A janela ainda existe? (fora do Windows ou sem handle: considera viva)."""
    if not hwnd:
        return True
    try:
        import ctypes
        return bool(ctypes.windll.user32.IsWindow(int(hwnd)))
    except Exception:
        return True

# Alvo de continuacao -> agente que sabe continuar nele
TARGET_AGENT = {"web": "WEB", "app": "DESKTOP", "code": "CODE", "folder": "FILE"}


CONTENT_MAX = 900     # conteudo literal guardado por pedido (mensagem, texto, busca)


@dataclass
class Turn:
    said: str
    resolved: str
    kind: str                     # new | continue | question | undo | clarify
    agents: list = field(default_factory=list)
    success: Optional[bool] = None
    summary: str = ""
    ts: float = field(default_factory=time.time)
    reply: str = ""               # o que o assistente respondeu (texto/voz)
    # Conteudo LITERAL que o pedido carregou (mensagem, texto ditado, busca, destinatario...).
    # "manda a mesma mensagem" depende disto: antes o contexto cortava o pedido em 160 letras.
    content: str = ""


class Session:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.id = uuid.uuid4().hex[:8]
        self.started_at = time.time()
        self.turns: list[Turn] = []
        self.web: Optional[dict] = None
        self.apps: dict[str, dict] = {}
        self.code: Optional[dict] = None
        self.folder: Optional[str] = None
        self.files: list[str] = []      # arquivos que o assistente criou nesta conversa (mais recente por ultimo)
        self.custom_title: Optional[str] = None   # nome dado pelo usuario (Renomear)
        self.focus: Optional[str] = None      # "web" | "app:<key>" | "code" | "folder"
        self.pending: Optional[dict] = None   # {"question", "task"}

    @property
    def empty(self) -> bool:
        return not self.turns and not self.pending

    # ── estado do mundo ───────────────────────────────────────────
    def remember_web(self, hwnd: int, url: str, title: str, visible: list[str]) -> None:
        self.web = {"hwnd": hwnd, "url": url, "title": title,
                    "visible": visible[:25], "ts": time.time()}
        self.focus = "web"

    def remember_app(self, key: str, hwnd: int, title: str, last_text: str = "") -> None:
        key = (key or "app").lower()
        self.apps[key] = {"hwnd": hwnd, "title": title, "last_text": last_text[:300],
                          "ts": time.time()}
        self.focus = f"app:{key}"

    def remember_code(self, folder: str, files: list[str]) -> None:
        self.code = {"folder": folder, "files": files[:40], "ts": time.time()}
        self.focus = "code"

    def remember_files(self, paths: list[str]) -> None:
        """Arquivos criados (planilha, site, script): "resume a planilha" le o arquivo, nao a tela."""
        for p in paths or []:
            if p and p not in self.files:
                self.files.append(p)
        self.files = self.files[-12:]

    def remember_folder(self, path: str) -> None:
        self.folder = path
        self.focus = "folder"

    # ── esclarecimento pendente ───────────────────────────────────
    def set_pending(self, question: str, task: str, target: Optional[str] = None) -> None:
        """target: alvo em que o pedido continuava (a resposta continua nele)."""
        self.pending = {"question": question, "task": task, "target": target}

    def clear_pending(self) -> None:
        self.pending = None

    # ── conversa ──────────────────────────────────────────────────
    def add_turn(self, said: str, resolved: str, kind: str, agents: list = None,
                 success: Optional[bool] = None, summary: str = "", content: str = "") -> None:
        self.turns.append(Turn(said, resolved, kind, list(agents or []), success,
                               (summary or "")[:400], content=(content or "")[:CONTENT_MAX]))
        self.turns = self.turns[-MAX_TURNS:]

    # ── alvos ─────────────────────────────────────────────────────
    def targets(self) -> dict[str, dict]:
        """Alvos de continuacao disponiveis: {"web": {...}, "app:notepad": {...}, ...}.
        Janelas que o usuario ja fechou saem da lista (nunca continuar no vazio)."""
        out = {}
        if self.web and _alive(self.web.get("hwnd")):
            out["web"] = {"type": "web", **self.web}
        for k, v in self.apps.items():
            if _alive(v.get("hwnd")):
                out[f"app:{k}"] = {"type": "app", "key": k, **v}
        if self.code:
            out["code"] = {"type": "code", **self.code}
        if self.folder:
            out["folder"] = {"type": "folder", "path": self.folder}
        return out

    def target(self, name: Optional[str]) -> Optional[dict]:
        if not name:
            return None
        return self.targets().get(name)

    @staticmethod
    def agent_for(target_name: Optional[str]) -> Optional[str]:
        if not target_name:
            return None
        return TARGET_AGENT.get(target_name.split(":")[0])

    # ── contexto para o modelo ────────────────────────────────────
    def context_block(self, max_chars: int = 3200) -> str:
        """Resumo da conversa + o que esta aberto (para resolver, voz e Maestro).
        Os pedidos recentes vao inteiros (com o conteudo literal); se passar do limite,
        saem os pedidos MAIS ANTIGOS — nunca o ultimo, o que esta aberto ou a pergunta pendente."""
        turns = []
        recent = self.turns[-6:]
        for i, t in enumerate(recent, 1):
            fresh = i > len(recent) - 3          # os 3 ultimos pedidos: sem cortar o essencial
            ok = "" if t.success is None else (" [ok]" if t.success else " [falhou]")
            g = [f"{i}. usuario: \"{t.said[:500 if fresh else 160]}\""]
            if t.resolved and t.resolved != t.said:
                g.append(f"   entendido: {t.resolved[:500 if fresh else 200]}")
            if t.content:
                g.append(f"   conteudo: {t.content[:CONTENT_MAX if fresh else 200]}")
            if t.agents:
                g.append(f"   agentes: {', '.join(t.agents)}{ok}")
            if t.summary:
                g.append(f"   resultado: {t.summary[:300]}")
            if t.reply:
                # o que o assistente disse (ofertas como "quer que eu toque o primeiro?"
                # tornam o "pode" seguinte entendivel)
                g.append(f"   assistente: \"{t.reply[:240 if fresh else 160]}\"")
            turns.append("\n".join(g))
        lines = []
        tg = self.targets()
        if tg:
            lines.append("ABERTO AGORA (alvos de continuacao):")
            for name, v in tg.items():
                mark = "  <- FOCO" if name == self.focus else ""
                if v["type"] == "web":
                    lines.append(f"- web: aba \"{v['title'][:80]}\" {v['url'][:120]}{mark}")
                    for item in v.get("visible", [])[:15]:
                        lines.append(f"    {item[:110]}")
                elif v["type"] == "app":
                    extra = f" | ultimo texto: \"{v['last_text'][:80]}\"" if v.get("last_text") else ""
                    lines.append(f"- {name}: janela \"{v['title'][:80]}\"{extra}{mark}")
                elif v["type"] == "code":
                    files = ", ".join(f.split("/")[-1].split("\\")[-1] for f in v.get("files", [])[:12])
                    lines.append(f"- code: projeto {v['folder']} ({files}){mark}")
                elif v["type"] == "folder":
                    lines.append(f"- folder: {v['path']}{mark}")
        if self.pending:
            lines.append(f"PERGUNTA PENDENTE: \"{self.pending['question']}\" "
                         f"(pedido original: \"{self.pending['task'][:400]}\")")
        tail = "\n".join(lines)
        while turns:
            text = "\n".join(["CONVERSA (mais antigo -> mais recente):"] + turns + ([tail] if tail else []))
            if len(text) <= max_chars or len(turns) == 1:
                return text[:max_chars] if len(turns) > 1 else text[-max_chars:]
            turns.pop(0)                         # sai o pedido mais antigo
        return tail[:max_chars]

    def set_last_reply(self, reply: str) -> None:
        if self.turns:
            self.turns[-1].reply = (reply or "")[:600]

    @property
    def title(self) -> str:
        if self.custom_title:
            return self.custom_title
        first = next((t.said for t in self.turns if t.said), "")
        return first[:80] or "Conversa"

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "started_at": self.started_at,
                "updated_at": time.time(), "focus": self.focus,
                "turns": [asdict(t) for t in self.turns],
                "web": self.web, "apps": self.apps, "code": self.code, "folder": self.folder,
                "files": self.files, "pending": self.pending, "custom_title": self.custom_title}

    # ── conversas salvas (barra lateral) ──────────────────────────
    def save(self, base: Path = SESSIONS_DIR) -> None:
        """Grava a conversa (so se tiver algum pedido). Escrita atomica."""
        if not self.turns:
            return
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"{self.id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        os.replace(tmp, path)

    def load(self, data: dict) -> None:
        """Retoma uma conversa salva. Janelas antigas so valem se ainda existirem
        (targets() descarta as fechadas)."""
        self.reset()
        self.id = data.get("id") or self.id
        self.started_at = data.get("started_at") or self.started_at
        fields = Turn.__dataclass_fields__
        self.turns = [Turn(**{k: v for k, v in t.items() if k in fields}) for t in data.get("turns", [])]
        self.web, self.apps = data.get("web"), data.get("apps") or {}
        self.code, self.folder = data.get("code"), data.get("folder")
        self.focus, self.pending = data.get("focus"), data.get("pending")
        self.files = list(data.get("files") or [])
        self.custom_title = data.get("custom_title")

    @staticmethod
    def list_saved(limit: int = 60, base: Path = SESSIONS_DIR) -> list[dict]:
        out = []
        if not base.is_dir():
            return out
        for f in base.glob("*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            out.append({"id": d.get("id", f.stem), "title": d.get("title", "Conversa"),
                        "updated_at": d.get("updated_at", f.stat().st_mtime),
                        "turns": len(d.get("turns", []))})
        out.sort(key=lambda x: x["updated_at"], reverse=True)
        return out[:limit]

    @staticmethod
    def rename_saved(sid: str, title: str, base: Path = SESSIONS_DIR) -> bool:
        data = Session.read_saved(sid, base)
        title = " ".join((title or "").split())[:80]
        if not data or not title:
            return False
        data["custom_title"] = data["title"] = title
        tmp = base / f"{sid}.tmp"
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        os.replace(tmp, base / f"{sid}.json")
        return True

    @staticmethod
    def delete_saved(sid: str, base: Path = SESSIONS_DIR) -> bool:
        """Tira da lista e move para memory/sessions/_excluidas (recuperavel, nunca apaga)."""
        if not sid or not all(c.isalnum() for c in sid):
            return False
        f = base / f"{sid}.json"
        if not f.is_file():
            return False
        trash = base / "_excluidas"
        trash.mkdir(parents=True, exist_ok=True)
        os.replace(f, trash / f.name)
        return True

    @staticmethod
    def read_saved(sid: str, base: Path = SESSIONS_DIR) -> Optional[dict]:
        if not sid or not all(c.isalnum() for c in sid):
            return None
        f = base / f"{sid}.json"
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
