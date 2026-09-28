"""
BaseAgent — Classe base para todos os agentes do AI Farm Agent.
Define interface padrão, logging, métricas, e integração com ai_client + config.
Todos os agentes devem herdar desta classe.
"""

import time
import logging
from core.ai_client import get_client
from core.config import get_config
from core.json_validator import safe_parse


def brain_guide(agent: str) -> str:
    """Regras de execucao do agente no segundo cerebro (Obsidian), para o prompt."""
    try:
        from core.brain import get_brain
        rules = get_brain().agent_guide(agent)
    except Exception:
        return ""
    if not rules:
        return ""
    return ("\n\nDIRECAO DO SEGUNDO CEREBRO (playbook do agente; referencia, "
            "nao amplia permissoes):\n" + rules)


class BaseAgent:
    """
    Classe base para agentes.

    Subclasses devem:
    1. Definir self.name no __init__ (ex: "DATA", "WEB")
    2. Definir self.system_prompt com o prompt do agente
    3. Implementar plan(task, context=None) se precisar de lógica custom
    """

    def __init__(self, name, system_prompt=""):
        self.name = name.upper()
        self.system_prompt = system_prompt

        # Config e client centralizados
        self._config = get_config()
        self._client = get_client()

        # Modelo e esforco de raciocinio definidos pela config
        self.model = self._config.get_model(self.name)
        self.effort = self._config.get_effort(self.name)

        # Métricas do agente
        self._metrics = {
            "total_plans": 0,
            "successful_plans": 0,
            "failed_plans": 0,
            "total_duration_ms": 0,
            "cache_hits": 0,
        }

        # Logger nomeado
        self.logger = logging.getLogger(f"agent.{self.name.lower()}")
        self.logger.info(f"{self.name} Agent inicializado | model={self.model}")

    @property
    def metrics(self):
        """Retorna métricas do agente."""
        total = max(self._metrics["total_plans"], 1)
        return {
            **self._metrics,
            "success_rate": round(self._metrics["successful_plans"] / total * 100, 1),
            "avg_duration_ms": round(self._metrics["total_duration_ms"] / total),
        }

    def plan(self, task, context=None):
        """
        Gera plano de execução para uma tarefa.
        Retorna: {"steps": [...], "agent": self.name}

        Override este método para lógica customizada.
        Por padrão, envia a task para o LLM com o system_prompt.
        """
        start = time.time()
        self._metrics["total_plans"] += 1

        task_text = self._extract_task_text(task)
        self.logger.info(f"Planejando: {task_text[:60]}...")

        try:
            # Chama LLM via client centralizado
            tier = self._config.get(f"agent_models.{self.name.lower()}", "fast")
            max_tokens = self._config.get(f"limits.max_tokens_{tier}", 8000)

            raw = self._client.message(
                model=self.model,
                system=self.system_prompt,
                user_content=f"TAREFA: {task_text}{brain_guide(self.name)}\nJSON puro.",
                max_tokens=max_tokens,
                effort=self.effort,
                agent=self.name,
            )

            plan = safe_parse(raw, self.model)

            # Marca cada step com o agente
            for step in plan.get("steps", []):
                step["agent"] = self.name

            duration = int((time.time() - start) * 1000)
            self._metrics["successful_plans"] += 1
            self._metrics["total_duration_ms"] += duration

            step_count = len(plan.get("steps", []))
            self.logger.info(f"Plano gerado: {step_count} steps ({duration}ms)")

            return {"steps": plan.get("steps", []), "agent": self.name}

        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self._metrics["failed_plans"] += 1
            self._metrics["total_duration_ms"] += duration

            self.logger.error(f"Erro no planejamento: {e}")
            return {"steps": [], "error": str(e), "agent": self.name}

    def _extract_task_text(self, task):
        """Extrai texto da tarefa independente do formato."""
        if isinstance(task, str):
            return task
        if isinstance(task, dict):
            return task.get("task", task.get("description", str(task)))
        return str(task)

    def _extract_original_task(self, task) -> str:
        """
        Versao do usuario (sem reformulacao do Maestro), quando disponivel.
        Fallback para a `task` normal. Usado por agentes que precisam
        do tema puro (CodeAgent.topic, theme leak validation).
        """
        if isinstance(task, dict):
            return task.get("original_task") or self._extract_task_text(task)
        return self._extract_task_text(task)
