"""
Controller — orquestra agentes e emite eventos para o EventBus.

E o equivalente desktop do antigo `ui/server.py:_run()`. Mesma logica de
execucao, mesmos contratos, MESMOS modulos do core/agents (zero
modificacao). A unica diferenca: em vez de `socketio.emit('phase', ...)`,
chamamos `bus.emit('phase', ...)`.

Mantem 1-pra-1 os eventos esperados pelo antigo frontend, mais 2 novos:
    log              — feed estruturado (level/agent/msg/ts)
    history_changed  — uma execucao foi gravada no historico
"""

from __future__ import annotations

import os
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from desktop.event_bus import bus
from desktop import history_store


# Imports dos agentes/core acontecem dentro do __init__ para evitar
# carregar dependencias pesadas (anthropic, playwright) ao importar este
# modulo em testes.

NO_SCREENSHOT = {
    "wait", "hotkey", "type_text", "app_type", "app_search", "focus_window",
    "vision_click", "vision_type", "uia_click", "uia_type", "run_python",
    "run_command", "write_file", "create_folder", "read_file", "list_files",
    "move_file", "copy_file", "delete_file", "find_files", "pip_install",
    "excel_write", "wait_for_window", "wait_for_element", "browser_read", "open_path", "browser_task", "app_task", "edit_project",
    "revert_project", "blank_document",
}
RETRY_ACTIONS = {"vision_click", "vision_type", "uia_click", "uia_type", "browser_click"}


MAX_TASK_LENGTH = 2000
TASK_TIMEOUT_S = 120


class Controller:
    """Coracao do desktop. Executa tarefas em background e publica eventos."""

    def __init__(self) -> None:
        from agents.maestro import Maestro
        from agents.data_agent import DataAgent
        from agents.web_agent import WebAgent
        from agents.code_agent import CodeAgent
        from agents.desktop_agent import DesktopAgent
        from agents.file_agent import FileAgent
        from core.automation import AutomationEngine
        from core.capture import ScreenCapture
        from core.narrator import ReportNarrator
        from core.context_manager import ContextManager
        from core.ai_client import get_client
        from agents.memory_agent import MemoryAgent

        self._ContextManager = ContextManager
        self._ai_client = get_client()
        self.memory = MemoryAgent()
        from core.brain import get_brain
        self._brain = get_brain()
        self.maestro = Maestro(memory=self.memory)
        self.agents = {
            "DATA": DataAgent(),
            "WEB": WebAgent(),
            "CODE": CodeAgent(),
            "DESKTOP": DesktopAgent(),
            "FILE": FileAgent(),
        }
        self.engine = AutomationEngine()
        self.capture = ScreenCapture()
        self.narrator = ReportNarrator()

        # Cleanup automatico de arquivos antigos no startup
        try:
            from scripts.cleanup_old_files import run_cleanup
            stats = run_cleanup(verbose=False)
            if stats["removed"]:
                print(f"  [cleanup] {stats['removed']} arquivos antigos removidos "
                      f"({stats['bytes_freed'] / 1024 / 1024:.1f} MB liberados)")
        except Exception as e:
            print(f"  [cleanup] falhou (nao critico): {e}")

        # Memoria: tira do caminho workflows de formatos antigos (v5-)
        try:
            moved = self.memory.purge_legacy()["moved"]
            if moved:
                print(f"  [memoria] {moved} workflow(s) de formato antigo movidos para .legacy/")
        except Exception as e:
            print(f"  [memoria] limpeza falhou (nao critico): {e}")

        # Conversa: o que foi feito e o que ficou aberto, entre pedidos
        from core.session import Session
        self.session = Session()
        # Pedido falado ja entendido COM a conversa (continua em qual alvo?): evita
        # a 2a chamada do resolvedor. Chave = texto do pedido; validado em followup.from_hint.
        self._voice_hints: Dict[str, dict] = {}

        self.state = {"running": False}
        self._lock = threading.Lock()
        # Cada execucao recebe um id. Uma thread cancelada que ainda esteja
        # presa (ex.: aguardando a API) nao pode emitir eventos na tela da
        # tarefa seguinte nem desligar o estado "running" dela.
        self._run_id = 0
        self._tls = threading.local()

    # ──────────────────────────────────────────────────────────────────
    #  API publica (consumida pela bridge QML)
    # ──────────────────────────────────────────────────────────────────

    def execute_task(self, task: str, dry_run: bool = False,
                     generate_report: bool = True) -> None:
        """Dispara execucao em thread separada."""
        task = (task or "").strip()
        if not task:
            bus.emit("error", {"msg": "Tarefa vazia."})
            return
        if len(task) > MAX_TASK_LENGTH:
            bus.emit("error",
                     {"msg": f"Tarefa muito longa (max {MAX_TASK_LENGTH} chars)."})
            return
        with self._lock:
            if self.state["running"]:
                bus.emit("error", {"msg": "Ja existe uma execucao em andamento."})
                return
            self.state["running"] = True
            self._run_id += 1
            run_id = self._run_id

        threading.Thread(
            target=self._run, args=(task, dry_run, generate_report, run_id),
            daemon=True,
        ).start()

    def voice_hint(self, text: str, hint: dict) -> None:
        """A voz avisa como o pedido foi entendido (kind/target) antes de envia-lo a tela."""
        self._voice_hints = {**dict(list(self._voice_hints.items())[-4:]), (text or "").strip(): hint}

    def new_session(self) -> None:
        """Nova conversa: esquece pedidos anteriores e o que estava aberto."""
        with self._lock:
            if self.state["running"]:
                return
        self.session.reset()
        bus.emit("session_reset", {"session": self.session.id})

    # ── conversas salvas ─────────────────────────────────────────────
    def list_conversations(self) -> list:
        from core.session import Session
        return Session.list_saved()

    def open_conversation(self, sid: str) -> Optional[dict]:
        """Retoma uma conversa salva: o historico volta para a tela e o contexto
        (pedidos, respostas, o que ainda estiver aberto) volta para o agente."""
        with self._lock:
            if self.state["running"]:
                return None
        from core.session import Session
        data = Session.read_saved(sid)
        if not data:
            return None
        self.session.load(data)
        bus.emit("session_reset", {"session": self.session.id, "loaded": True})
        return data

    def _after_turn(self, said: str, task: str, turn: dict, entry: dict) -> None:
        """Depois de cada pedido: a resposta do assistente (natural, como numa conversa)
        + gravar a conversa. Em segundo plano: nao atrasa o proximo pedido."""
        err = str(entry.get("error") or "")
        kind = turn.get("kind")

        def work():
            reply, speak = "", False
            try:
                if kind == "question":
                    reply = turn.get("summary", "")
                elif err.startswith("clarification"):
                    reply = (self.session.pending or {}).get("question", "")
                elif err.startswith("limitation"):
                    reply = err.split(":", 1)[-1].strip()
                elif kind != "cancel":
                    from core.reply import compose
                    recent = [t.reply for t in self.session.turns[-4:] if t.reply]
                    r = compose(said, task, turn.get("summary", ""), bool(entry.get("success")), err, recent)
                    reply, speak = r["text"], r["speak"]
                    bus.emit("assistant_message", {"said": said, "text": reply, "speak": speak,
                                                   "success": bool(entry.get("success"))})
                if reply:
                    self.session.set_last_reply(reply)
            except Exception as e:
                print(f"  [Resposta] falhou: {e}")
            finally:
                try:
                    self.session.save()
                    bus.emit("conversations_changed", {"id": self.session.id})
                except Exception as e:
                    print(f"  [Sessao] nao gravou: {e}")
        threading.Thread(target=work, daemon=True, name="assistant-reply").start()

    def force_stop(self) -> None:
        """Cancela execucao em andamento."""
        with self._lock:
            self.state["running"] = False
        bus.emit("cancelled", {"msg": "Execucao interrompida pelo usuario."})

    # ──────────────────────────────────────────────────────────────────
    #  Loop interno (porta de ui/server.py:_run)
    # ──────────────────────────────────────────────────────────────────

    def _is_current(self) -> bool:
        """True na thread da execucao ativa (ou fora de qualquer execucao)."""
        rid = getattr(self._tls, "run_id", None)
        return rid is None or rid == self._run_id

    def _alive(self) -> bool:
        """A execucao desta thread deve continuar?"""
        return self.state["running"] and self._is_current()

    def _emit(self, event: str, payload: Any = None) -> None:
        if self._is_current():
            bus.emit(event, payload)

    def _log(self, level: str, agent: str, msg: str,
             extra: Optional[Dict[str, Any]] = None) -> None:
        """Helper para emitir logs estruturados."""
        payload = {
            "ts": datetime.now().isoformat(timespec="milliseconds"),
            "level": level,
            "agent": agent,
            "msg": msg,
        }
        if extra:
            payload["extra"] = extra
        self._emit("log", payload)

    def _emit_usage(self) -> None:
        """Emite uso REAL agregado do AIClient (custo por modelo + tokens)."""
        m = self._ai_client.metrics
        payload = {
            "calls": m["total_calls"],
            "tokens_est": (m["total_input_tokens"] + m["total_output_tokens"]
                           + m.get("total_cache_read_tokens", 0)
                           + m.get("total_cache_write_tokens", 0)),
            "input_tokens": m["total_input_tokens"],
            "output_tokens": m["total_output_tokens"],
            "cache_read_tokens": m.get("total_cache_read_tokens", 0),
            "cost_usd": round(m["total_cost_usd"], 5),
            "by_model": m.get("calls_by_model", {}),
        }
        self._emit("api_usage", payload)

    @staticmethod
    def _metrics_delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uso de UMA execucao. O AIClient acumula desde a abertura do app;
        gravar o acumulado no historico fazia o total somar custos repetidos.
        """
        def d(key):
            return after.get(key, 0) - before.get(key, 0)

        by_agent = {}
        for agent, cur in after.get("calls_by_agent", {}).items():
            prev = before.get("calls_by_agent", {}).get(agent, {})
            calls = cur["calls"] - prev.get("calls", 0)
            if calls:
                by_agent[agent] = {
                    "calls": calls,
                    "cost_usd": round(cur["cost_usd"] - prev.get("cost_usd", 0.0), 6),
                }
        return {
            "api_calls": d("total_calls"),
            "tokens_est": (d("total_input_tokens") + d("total_output_tokens")
                           + d("total_cache_read_tokens") + d("total_cache_write_tokens")),
            "input_tokens": d("total_input_tokens"),
            "output_tokens": d("total_output_tokens"),
            "cache_read_tokens": d("total_cache_read_tokens"),
            "cache_write_tokens": d("total_cache_write_tokens"),
            "cost_usd": round(d("total_cost_usd"), 6),
            "by_agent": by_agent,
            "truncated": d("truncated"),
        }

    def _run_undo(self, dry_run: bool, turn: dict) -> bool:
        """"desfaz": volta a versao anterior do projeto de codigo da conversa."""
        code = self.session.code or {}
        folder = code.get("folder", "")
        turn["agents"].append("CODE")
        self._emit("plan_ready", {"plan": {
            "task_summary": "desfazer a ultima alteracao",
            "steps": [{"step": 1, "description": "[CODE] Voltar a versao anterior do projeto",
                       "action": "CODE"}],
            "skills": []}})
        self._emit("step_start", {"step": 1, "total": 1, "action": "revert_project",
                                  "desc": "[CODE] Voltar a versao anterior", "progress": 0})
        open_t = "index.html" if os.path.exists(os.path.join(folder, "index.html")) else ""
        r = self.engine.execute("revert_project", {"folder": folder, "open": open_t}, dry_run=dry_run)
        self._emit("step_done", {"step": 1, "total": 1, "ok": r.get("success", False),
                                 "result": r.get("result", ""), "action": "revert_project",
                                 "desc": "[CODE] Voltar a versao anterior", "progress": 100})
        turn["summary"] = str(r.get("result", ""))[:300]
        self._emit("task_done", {"msg": "Concluido.", "steps": 1, "dry_run": dry_run})
        return bool(r.get("success"))

    def _run(self, task: str, dry_run: bool, gen_report: bool,
             run_id: int = 0) -> None:
        self._tls.run_id = run_id or self._run_id
        all_success = True
        task_start = time.time()
        metrics_before = self._ai_client.metrics
        entry = history_store.new_execution(task, dry_run=dry_run)
        brain_plan = None
        all_records: list = []
        said = task
        turn = {"kind": "new", "agents": [], "summary": "", "recorded": False}
        entry["session_id"] = self.session.id

        try:
            self._emit("phase", {"phase": "maestro", "msg": "Entendendo o pedido..."})
            self._log("INFO", "MAESTRO", f"Recebida tarefa: {task[:80]}")

            # Conversa: "agora abra esse segundo video" vira um pedido
            # completo, apontando para o que ficou aberto antes.
            from core.followup import from_hint, resolve
            res = from_hint(said, self.session, self._voice_hints.pop(said.strip(), None)) \
                or resolve(said, self.session)
            self._emit_usage()
            kind, target = res["kind"], res.get("target")
            turn["kind"] = kind
            if res.get("via") == "pending":
                self.session.clear_pending()
            if res["task"] != said or kind != "new":
                self._emit("resolved", {"said": said, "task": res["task"], "kind": kind,
                                        "target": target or ""})
                self._log("INFO", "MAESTRO", f"Entendido ({kind}): {res['task'][:120]}")
            task = res["task"]
            entry["resolved"] = task

            if kind == "cancel":
                self._emit("answer", {"msg": "Nada em execução para parar."})
                entry["success"] = True
                turn["recorded"] = True     # nao entra na conversa
                return
            if kind == "question":
                self._emit("answer", {"msg": res["answer"]})
                turn["summary"] = res["answer"]
                entry["success"] = True
                return
            if kind == "clarify":
                self.session.set_pending(res["question"], task, target)
                self._emit("error", {"msg": res["question"], "kind": "clarification"})
                entry["error"] = "clarification_required"
                turn["recorded"] = True     # a resposta continua o pedido (pending)
                return
            if kind == "undo":
                ok = self._run_undo(dry_run, turn)
                entry["success"] = ok
                return

            self._emit("phase", {"phase": "maestro", "msg": "Analisando intencao..."})
            # Memoria: o Maestro consulta rotas parecidas e as usa como
            # referencia no prompt (nunca como atalho).
            conversation = "" if self.session.empty else self.session.context_block()
            plan = self.maestro.analyze(task, conversation=conversation,
                                        continue_in=target or "")
            self._emit_usage()
            maestro_skills = self._brain.last_skills.pop("MAESTRO", [])
            if maestro_skills:
                self._log("INFO", "MAESTRO", "Skills aplicadas: " + ", ".join(maestro_skills))
                entry.setdefault("agent_skills", {})["MAESTRO"] = maestro_skills

            if plan.get("needs_clarification"):
                question = plan.get("question", "Tarefa ambigua — pode dar mais detalhes?")
                # A resposta do usuario continua ESTE pedido (sem redigitar tudo)
                self.session.set_pending(question, task, target)
                self._emit("error", {"msg": question, "kind": "clarification"})
                entry["error"] = "clarification_required"
                turn["recorded"] = True     # a resposta continua o pedido (pending)
                return

            if plan.get("limitation"):
                # Pedido que o sistema nao cumpre como foi feito (ex.: letra
                # de musica protegida). Aviso honesto em vez de substituto.
                self._emit("error", {"msg": plan.get("message", ""), "kind": "limitation"})
                entry["error"] = "limitation: " + plan.get("message", "")
                return

            if plan.get("error"):
                if plan.get("rejected_plan"):
                    brain_plan = self._brain.write_plan(task, plan["rejected_plan"])
                self._emit("error", {"msg": plan.get("message", "Erro do Maestro.")})
                entry["error"] = plan.get("message", "maestro_error")
                return

            # Plano proposto e validado vai para o segundo cerebro antes de
            # executar; cada agente anexa seus passos e a validacao.
            brain_plan = self._brain.write_plan(task, plan)

            subtasks = plan.get("subtasks", [])
            entry["subtasks"] = [
                {"agent": s.get("agent", ""), "task": s.get("task", "")}
                for s in subtasks
            ]
            entry["skills"] = plan.get("skills", [])

            self._emit("plan_ready", {"plan": {
                "task_summary": plan.get("analysis", ""),
                "steps": [
                    {
                        "step": i + 1,
                        "description": f"[{s['agent']}] {s['task']}",
                        "action": s["agent"],
                    }
                    for i, s in enumerate(subtasks)
                ],
                "skills": plan.get("skills", []),
            }})

            self.capture.clear_records()
            all_records = []
            step_n = 0
            ctx_mgr = self._ContextManager()
            cont_target = self.session.target(target)
            cont_used = False

            for si, subtask in enumerate(subtasks):
                if not self._alive():
                    self._emit("cancelled", {"msg": "Cancelado."})
                    return

                subtask = ctx_mgr.prepare_subtask(subtask, si)

                agent_name = subtask.get("agent", "").upper()
                agent = self.agents.get(agent_name)
                if not agent:
                    all_success = False
                    self._log("WARN", "MAESTRO",
                              f"Agente desconhecido: {agent_name}")
                    continue

                subtask_params = dict(subtask.get("params", {}) or {})
                # Continuacao: entrega ao agente o alvo ja aberto (aba, janela, projeto)
                from core.routing import continue_target_for
                tgt, why = continue_target_for(self.session, agent_name, subtask_params, target,
                                               task, cont_used)
                if tgt:
                    subtask_params["continue"] = tgt
                    subtask["params"] = subtask_params
                    cont_used = cont_used or why == "resolver"
                    self._log("INFO", agent_name, f"Continuando em: {tgt.get('key') or tgt['type']} ({why})")
                turn["agents"].append(agent_name)
                agent_task = subtask.get("task", "")
                # Versao original (do usuario) — usada por agentes que precisam
                # do tema puro (CodeAgent: topic + theme leak). O Maestro
                # garante via `setdefault` no analyze(). Fallback para `task`.
                original_task = subtask.get("original_task", agent_task)
                dep = subtask.get("depends_on")

                self._emit("phase", {"phase": "agent", "msg": f"{agent_name} Agent..."})
                self._log("INFO", agent_name, f"Iniciando: {agent_task[:80]}")

                legacy_ctx = None
                if dep is not None:
                    try:
                        extracted = ctx_mgr.get(int(dep))
                        if extracted:
                            legacy_ctx = {
                                "agent": extracted.get("agent"),
                                "results": extracted.get("output", []),
                                "files": extracted.get("files", []),
                                "folder": extracted.get("folder"),
                                "primary_path": extracted.get("primary_path"),
                                "url": extracted.get("url"),
                            }
                    except (ValueError, TypeError):
                        pass

                # Plano do agente
                if agent_name == "DESKTOP" and subtask_params.get("app"):
                    agent_plan = agent.plan(
                        {"task": agent_task, "params": subtask_params,
                         "original_task": original_task},
                        context=subtask_params,
                    )
                else:
                    # Propaga `original_task` no payload do agente. Agentes
                    # que ignoram esse campo continuam funcionando normal
                    # (backward-compat).
                    payload = {"task": agent_task, "original_task": original_task,
                               "params": subtask_params}
                    agent_plan = agent.plan(payload, context=legacy_ctx)
                self._emit_usage()

                # Rastro dos 3 subagentes do agente (entender/montar/conferir)
                sub_traces = agent_plan.get("subagents") or []
                if sub_traces:
                    from agents.subagents import summarize
                    self._log("INFO", agent_name, "Subagentes: " + summarize(sub_traces))

                if agent_plan.get("error") or not agent_plan.get("steps"):
                    # Plano vazio/falho = subtask nao executada. Antes isso
                    # nao marcava falha e a tarefa ia para a memoria como
                    # "sucesso".
                    all_success = False
                    self._log("ERROR", agent_name,
                              f"Plano falhou: {agent_plan.get('error') or agent_plan.get('reason') or 'sem steps'}")
                    continue

                agent_steps = agent_plan.get("steps", [])

                # O agente propoe; o Maestro valida os passos contra as
                # politicas antes de qualquer acao no computador.
                from core.plan_validator import validate_steps
                step_check = validate_steps(agent_name, subtask, agent_steps, task)
                used_skills = self._brain.last_skills.pop(agent_name, [])
                if used_skills:
                    self._log("INFO", agent_name, "Skills aplicadas: " + ", ".join(used_skills))
                    entry.setdefault("agent_skills", {})[agent_name] = used_skills
                self._brain.append_agent_plan(brain_plan, agent_name, subtask,
                                              agent_steps, step_check, sub_traces)
                if not step_check.approved:
                    all_success = False
                    self._log("WARN", "MAESTRO",
                              f"Passos do agente {agent_name} reprovados: {step_check.summary()}")
                    if hasattr(agent, "report_result") and not dry_run:
                        agent.report_result({"task": agent_task}, False)
                    continue

                sub_results = []
                sub_ok = True
                is_desktop = agent_name == "DESKTOP"
                ws_snapshot = dict(self.engine.workspace)
                # Acoes longas (piloto do navegador) param no Esc e narram cada turno
                self.engine.should_stop = lambda: not self._alive()
                self.engine.on_progress = (
                    lambda msg, _a=agent_name: self._log("INFO", _a, msg))

                for j, step in enumerate(agent_steps):
                    if not self._alive():
                        self._emit("cancelled", {"msg": "Cancelado."})
                        return
                    step_n += 1
                    action = step.get("action", "")
                    params = step.get("params", {})
                    desc = step.get("description", "")
                    start_time = time.time()

                    self._emit("step_start", {
                        "step": step_n,
                        "total": step_n + len(agent_steps) - j - 1,
                        "desc": f"[{agent_name}] {desc}",
                        "action": action,
                        "progress": round(si / max(1, len(subtasks)) * 100),
                    })

                    result = self.engine.execute(action, params, dry_run=dry_run)

                    # Retry para acoes visuais
                    if (not result.get("success", True)
                            and action in RETRY_ACTIONS and not dry_run
                            and not str(result.get("result", "")).startswith("⛔")):
                        time.sleep(2)
                        result = self.engine.execute(action, params, dry_run=dry_run)

                    # Subagente de conferencia pos-passo (ex.: ContentGuard do
                    # WebAgent marca prompt injection no conteudo lido).
                    if hasattr(agent, "review_step"):
                        result = agent.review_step(step, result)

                    if not result.get("success", True):
                        all_success = False
                        sub_ok = False
                        self._log("WARN", agent_name,
                                  f"Step falhou: {action}",
                                  {"error": result.get("error", "")})
                    else:
                        self._log("INFO", agent_name, f"OK: {action}")

                    duration = int((time.time() - start_time) * 1000)
                    try:
                        from core.action_logger import log_action
                        log_action(agent_name, action, params, result,
                                   duration_ms=duration)
                    except Exception:
                        pass

                    all_records.append(result)
                    sub_results.append(result.get("result", ""))

                    cap = None
                    if (not dry_run and action not in NO_SCREENSHOT
                            and not is_desktop):
                        try:
                            cap = self.capture.capture_step(
                                step_n, desc, action, result.get("result", "")
                            )
                        except Exception:
                            pass

                    self._emit("step_done", {
                        "step": step_n,
                        "total": step_n + len(agent_steps) - j - 1,
                        "ok": result.get("success", False),
                        "result": result.get("result", ""),
                        "desc": f"[{agent_name}] {desc}",
                        "action": action,
                        "screenshot": (cap.get("filename")
                                       if cap and cap.get("filename") else None),
                        "progress": round((si + 1) / max(1, len(subtasks)) * 100),
                    })
                    time.sleep(0.05)

                if not dry_run and hasattr(agent, "report_result"):
                    agent.report_result({"task": agent_task}, sub_ok)

                if not dry_run:
                    extracted = ctx_mgr.extract(
                        subtask_index=si,
                        agent_name=agent_name,
                        step_results=sub_results,
                        engine_workspace=self.engine.workspace,
                        workspace_snapshot=ws_snapshot,
                    )
                    if (extracted.get("files") or extracted.get("folder")
                            or extracted.get("url")):
                        self._emit("context_extracted", {
                            "subtask": si + 1,
                            "agent": agent_name,
                            "folder": extracted.get("folder"),
                            "files": extracted.get("files", []),
                            "primary_path": extracted.get("primary_path"),
                            "url": extracted.get("url"),
                        })
                        # Acumula no historico
                        if extracted.get("folder"):
                            entry["artifacts"]["folder"] = extracted.get("folder")
                        if extracted.get("files"):
                            entry["artifacts"]["files"] = extracted.get("files", [])
                        if extracted.get("url"):
                            entry["artifacts"]["url"] = extracted.get("url")
                    # O que ficou aberto vira contexto do proximo pedido
                    from core.observer import observe
                    seen = observe(agent_name, subtask_params, extracted, self.session)
                    if seen:
                        self._log("INFO", agent_name, f"Sessao: {seen}")
                    if extracted.get("summary") or extracted.get("text"):
                        turn["summary"] = extracted.get("summary") or extracted.get("text", "")[:400]

            # Restaura browser SO no final
            if getattr(self.engine, "vision", None):
                try:
                    self.engine.vision.restore_browser()
                except Exception:
                    pass

            if not dry_run:
                # Registra a ROTA (agentes + tipo de acao, sem conteudo) com
                # o resultado. Falhas tambem contam: rota que falha mais do
                # que funciona deixa de ser sugerida ao Maestro.
                try:
                    mem = self.memory.record(task, subtasks, all_success)
                    if mem.get("saved"):
                        self._log("INFO", "MEMORY",
                                  f"Rota registrada ({'sucesso' if all_success else 'falha'})")
                except Exception as mem_err:
                    self._log("WARN", "MEMORY", f"Falha ao registrar rota: {mem_err}")

            # NB: o registro de execucoes vive em desktop/history_store.py
            # (gravado no finally desta funcao). Aprendizado de rotas vive
            # em memory/workflow_store v6.

            self._emit("task_done", {
                "msg": "Concluido.",
                "steps": step_n,
                "dry_run": dry_run,
                "skills": plan.get("skills", []),
                "context_summary": ctx_mgr.summary(),
            })
            self._log("INFO", "SYSTEM",
                      f"Execucao concluida em {step_n} step(s).")

            if gen_report and not dry_run:
                self._emit("phase", {"phase": "reporting",
                                   "msg": "Gerando relatorio..."})
                report = self.narrator.generate_report(
                    task, all_records, self.capture.get_captures_as_base64(3)
                )
                self._emit("report_ready", {"report": report})

            entry["success"] = all_success

        except Exception as e:
            tb = traceback.format_exc()
            self._emit("error", {"msg": str(e), "trace": tb})
            self._log("ERROR", "SYSTEM", f"Excecao: {e}", {"trace": tb})
            entry["error"] = str(e)
        finally:
            with self._lock:
                if self._is_current():
                    self.state["running"] = False
            # Conversa: este pedido vira contexto do proximo (mesmo se falhou)
            if not turn["recorded"]:
                try:
                    self.session.add_turn(said, task, turn["kind"], turn["agents"],
                                          entry.get("success"), turn["summary"]
                                          or entry.get("error") or "")
                except Exception as sess_err:
                    print(f"  [Sessao] Falhou ao registrar: {sess_err}")
            entry["ended_at"] = datetime.now().isoformat(timespec="seconds")
            entry["duration_ms"] = int((time.time() - task_start) * 1000)
            # Metricas REAIS desta execucao (delta do AIClient)
            entry["metrics"] = self._metrics_delta(
                metrics_before, self._ai_client.metrics)
            try:
                history_store.append(entry)
                self._emit("history_changed", {"entry": entry})
            except Exception as hist_err:
                print(f"  [History] Falhou ao gravar: {hist_err}")
            # Segundo cerebro: plano vira "executado"/"falhou" e a execucao
            # entra em 40 Execucoes/Sucesso ou Falhas (consulta futura).
            if not str(entry.get("error") or "").startswith(("clarification", "limitation")):
                try:
                    self._brain.finish(brain_plan, entry, all_records)
                except Exception as brain_err:
                    print(f"  [Brain] Falhou ao registrar: {brain_err}")
            if not turn["recorded"]:
                self._after_turn(said, task, turn, entry)
