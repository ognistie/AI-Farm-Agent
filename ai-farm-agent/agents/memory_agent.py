"""
Memory Agent — Consulta workflows salvos antes de replanejar.
"""

from memory.workflow_store import find_similar_workflow, save_workflow


class MemoryAgent:
    def __init__(self):
        self.name = "MEMORY"

    def find_template(self, task):
        """Busca workflow similar ja executado com sucesso."""
        wf = find_similar_workflow(task)
        if wf:
            print(f"  [MEMORY] Template encontrado: {wf.get('task','')[:50]}")
            return {"found": True, "workflow": wf}
        return {"found": False}

    def save_success(self, task, steps, agent):
        """Salva workflow bem-sucedido para reuso."""
        try:
            save_workflow(task, steps, agent, success=True)
            print(f"  [MEMORY] Workflow salvo: {task[:40]}")
        except Exception as e:
            print(f"  [MEMORY] Erro ao salvar: {e}")