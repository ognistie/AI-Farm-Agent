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
    "excel_write", "wait_for_window", "wait_for_element",
}
RETRY_ACTIONS = {"vision_click", "vision_type", "uia_click", "uia_type"}

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

        self._ContextManager = ContextManager
        self._ai_client = get_client()
        self.maestro = Maestro()
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

        self.state = {"running": False}
        self._lock = threading.Lock()

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

        threading.Thread(
            target=self._run, args=(task, dry_run, generate_report),
            daemon=True,
        ).start()

    def force_stop(self) -> None:
        """Cancela execucao em andamento."""
        with self._lock:
            self.state["running"] = False
        bus.emit("cancelled", {"msg": "Execucao interrompida pelo usuario."})

    # ──────────────────────────────────────────────────────────────────
    #  Loop interno (porta de ui/server.py:_run)
    # ──────────────────────────────────────────────────────────────────

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
        bus.emit("log", payload)

    def _emit_usage(self) -> None:
        """Emite uso REAL agregado do AIClient (custo por modelo + tokens)."""
        m = self._ai_client.metrics
        payload = {
            "calls": m["total_calls"],
            "tokens_est": m["total_input_tokens"] + m["total_output_tokens"],
            "input_tokens": m["total_input_tokens"],
            "output_tokens": m["total_output_tokens"],
            "cost_usd": round(m["total_cost_usd"], 5),
            "by_model": m.get("calls_by_model", {}),
            "fallbacks": m.get("fallbacks", 0),
        }
        bus.emit("api_usage", payload)

    def _run(self, task: str, dry_run: bool, gen_report: bool) -> None:
        all_success = True
        task_start = time.time()
        entry = history_store.new_execution(task, dry_run=dry_run)

        try:
            bus.emit("phase", {"phase": "maestro", "msg": "Analisando intencao..."})
            self._log("INFO", "MAESTRO", f"Recebida tarefa: {task[:80]}")

            # Memoria: workflow_store v4 ja gerencia reaproveitamento via Maestro.
            # O Maestro consulta find_similar_workflow internamente e devolve plano
            # se houver match com mesmo tema. Aqui apenas analisamos normalmente.
            plan = self.maestro.analyze(task)
            self._emit_usage()

            if plan.get("needs_clarification"):
                bus.emit("error", {
                    "msg": plan.get("question",
                                    "Tarefa ambigua — pode dar mais detalhes?"),
                    "kind": "clarification",
                })
                entry["error"] = "clarification_required"
                return

            if plan.get("error"):
                bus.emit("error", {"msg": plan.get("message", "Erro do Maestro.")})
                entry["error"] = plan.get("message", "maestro_error")
                return

            subtasks = plan.get("subtasks", [])
            entry["subtasks"] = [
                {"agent": s.get("agent", ""), "task": s.get("task", "")}
                for s in subtasks
            ]
            entry["skills"] = plan.get("skills", [])

            bus.emit("plan_ready", {"plan": {
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

            for si, subtask in enumerate(subtasks):
                if not self.state["running"]:
                    bus.emit("cancelled", {"msg": "Cancelado."})
                    return

                subtask = ctx_mgr.prepare_subtask(subtask, si)

                agent_name = subtask.get("agent", "").upper()
                agent = self.agents.get(agent_name)
                if not agent:
                    self._log("WARN", "MAESTRO",
                              f"Agente desconhecido: {agent_name}")
                    continue

                subtask_params = subtask.get("params", {}) or {}
                agent_task = subtask.get("task", "")
                # Versao original (do usuario) — usada por agentes que precisam
                # do tema puro (CodeAgent: topic + theme leak). O Maestro
                # garante via `setdefault` no analyze(). Fallback para `task`.
                original_task = subtask.get("original_task", agent_task)
                dep = subtask.get("depends_on")

                bus.emit("phase", {"phase": "agent", "msg": f"{agent_name} Agent..."})
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
                    payload = {"task": agent_task, "original_task": original_task}
                    agent_plan = agent.plan(payload, context=legacy_ctx)
                self._emit_usage()

                if agent_plan.get("error"):
                    self._log("ERROR", agent_name,
                              f"Plano falhou: {agent_plan.get('error')}")
                    continue

                agent_steps = agent_plan.get("steps", [])
                sub_results = []
                is_desktop = agent_name == "DESKTOP"
                ws_snapshot = dict(self.engine.workspace)

                for j, step in enumerate(agent_steps):
                    if not self.state["running"]:
                        bus.emit("cancelled", {"msg": "Cancelado."})
                        return
                    step_n += 1
                    action = step.get("action", "")
                    params = step.get("params", {})
                    desc = step.get("description", "")
                    start_time = time.time()

                    bus.emit("step_start", {
                        "step": step_n,
                        "total": step_n + len(agent_steps) - j - 1,
                        "desc": f"[{agent_name}] {desc}",
                        "action": action,
                        "progress": round(si / max(1, len(subtasks)) * 100),
                    })

                    result = self.engine.execute(action, params, dry_run=dry_run)

                    # Retry para acoes visuais
                    if (not result.get("success", True)
                            and action in RETRY_ACTIONS and not dry_run):
                        time.sleep(2)
                        result = self.engine.execute(action, params, dry_run=dry_run)

                    if not result.get("success", True):
                        all_success = False
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

                    bus.emit("step_done", {
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
                        bus.emit("context_extracted", {
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

            # Restaura browser SO no final
            if getattr(self.engine, "vision", None):
                try:
                    self.engine.vision.restore_browser()
                except Exception:
                    pass

            if all_success and not dry_run:
                try:
                    from memory.workflow_store import save_workflow
                    save_workflow(
                        task,
                        [r.get("result", "") for r in all_records],
                        subtasks[0].get("agent", "") if subtasks else "",
                        True,
                    )
                except Exception:
                    pass

            # NB: o registro de execucoes vive em desktop/history_store.py
            # (gravado no finally desta funcao). Removido o EvolutionEngine
            # duplicado — todo aprendizado agora vive em memory/workflow_store v4.

            bus.emit("task_done", {
                "msg": "Concluido.",
                "steps": step_n,
                "dry_run": dry_run,
                "skills": plan.get("skills", []),
                "context_summary": ctx_mgr.summary(),
            })
            self._log("INFO", "SYSTEM",
                      f"Execucao concluida em {step_n} step(s).")

            if gen_report and not dry_run:
                bus.emit("phase", {"phase": "reporting",
                                   "msg": "Gerando relatorio..."})
                report = self.narrator.generate_report(
                    task, all_records, self.capture.get_captures_as_base64(3)
                )
                bus.emit("report_ready", {"report": report})

            entry["success"] = all_success

        except Exception as e:
            tb = traceback.format_exc()
            bus.emit("error", {"msg": str(e), "trace": tb})
            self._log("ERROR", "SYSTEM", f"Excecao: {e}", {"trace": tb})
            entry["error"] = str(e)
        finally:
            with self._lock:
                self.state["running"] = False
            entry["ended_at"] = datetime.now().isoformat(timespec="seconds")
            entry["duration_ms"] = int((time.time() - task_start) * 1000)
            # Metricas REAIS por modelo + custo exato (vindo do AIClient)
            m = self._ai_client.metrics
            entry["metrics"] = {
                "api_calls": m["total_calls"],
                "tokens_est": m["total_input_tokens"] + m["total_output_tokens"],
                "input_tokens": m["total_input_tokens"],
                "output_tokens": m["total_output_tokens"],
                "cost_usd": round(m["total_cost_usd"], 6),
                "by_model": dict(m.get("calls_by_model", {})),
                "fallbacks": m.get("fallbacks", 0),
            }
            try:
                history_store.append(entry)
                bus.emit("history_changed", {"entry": entry})
            except Exception as hist_err:
                print(f"  [History] Falhou ao gravar: {hist_err}")
