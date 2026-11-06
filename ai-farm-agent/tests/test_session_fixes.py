"""Os erros do teste de conversa de 2026-11-05, reproduzidos sem abrir nada na tela."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import existing_targets as E


class Tree(unittest.TestCase):
    """Area de Trabalho falsa: trabalhos/{docs, fotos, site} e um projeto criado na conversa."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.desktop = root / "Desktop"
        self.trabalhos = self.desktop / "trabalhos"
        for name in ("docs", "fotos", "site"):
            (self.trabalhos / name).mkdir(parents=True)
        self.project = root / "Documents" / "AI Farm Agent" / "site_exemplo"
        self.project.mkdir(parents=True)
        (self.project / "index.html").write_text("<html></html>")
        folders = {"Desktop": str(self.desktop), "Documents": str(root / "Documents")}
        patcher = patch.object(E, "known_folder", side_effect=lambda key: folders.get(key, str(root)))
        patcher.start()
        self.addCleanup(patcher.stop)
        windows = patch.object(E, "_windows_titled", return_value=[])
        self.windows = windows.start()
        self.addCleanup(windows.stop)
        self.session = SimpleNamespace(code={"folder": str(self.project), "files": []}, folder=None)

    def plan(self, text, session="default"):
        return E.existing_plan(text, self.session if session == "default" else session)

    def opened(self, plan):
        self.assertIsNotNone(plan)
        self.assertNotIn("needs_clarification", plan, plan)
        existing = plan["subtasks"][0]["params"]["existing"]
        self.assertEqual(plan["subtasks"][0]["agent"], "DESKTOP")
        return existing.get("path") or existing.get("title")


class OpeningWhatExists(Tree):
    def test_site_in_the_browser_opens_the_project_page_not_a_new_project(self):
        for said in ("abrir o resultado do site no navegador para ver o projeto",
                     "executar o programa do site no projeto", "abre o site no Chrome"):
            self.assertEqual(self.opened(self.plan(said)), str(self.project / "index.html"), said)

    def test_project_folder_opens_the_real_folder(self):
        for said in ("abrir a pasta dos arquivos do projeto no explorador de arquivos", "abre a pasta do site",
                     "mostra a pasta que você criou"):
            self.assertEqual(self.opened(self.plan(said)), str(self.project), said)

    def test_without_a_project_it_asks_instead_of_inventing_one(self):
        session = SimpleNamespace(code=None, folder=None)
        for said in ("abrir a pasta do projeto", "abrir o site do projeto no navegador"):
            plan = self.plan(said, session)
            self.assertTrue(plan["needs_clarification"], said)
            self.assertIn("projeto", plan["question"])

    def test_subfolder_inside_another_on_the_desktop(self):
        # Real: virou o caminho "Desktop\\docs dentro de trabalhos"
        self.assertEqual(self.opened(self.plan("abrir a pasta 'docs' dentro da pasta trabalhos na Área de Trabalho")),
                         str(self.trabalhos / "docs"))

    def test_missing_subfolder_lists_what_exists(self):
        plan = self.plan("abrir a pasta contratos dentro da pasta trabalhos na area de trabalho")
        self.assertTrue(plan["needs_clarification"])
        self.assertIn("docs, fotos, site", plan["question"])

    def test_folder_changed_at_a_time(self):
        target = self.trabalhos / "fotos"
        stamp = time.mktime((2026, 11, 5, 16, 30, 0, 0, 0, -1))
        os.utime(target, (stamp, stamp))
        for other in ("docs", "site"):
            os.utime(self.trabalhos / other, (stamp - 7200, stamp - 7200))
        for said in ("abrir a segunda pasta dentro da pasta trabalhos, a que foi alterada às 16:30",
                     "abre a pasta dentro da trabalhos que foi alterada às 16 e 30"):
            self.assertEqual(self.opened(self.plan(said)), str(target), said)

    def test_ordinal_alone_asks_because_the_order_depends_on_the_screen(self):
        plan = self.plan("abrir a segunda pasta dentro da pasta trabalhos")
        self.assertTrue(plan["needs_clarification"])
        self.assertIn("docs", plan["question"])

    def test_taskbar_icon_brings_the_open_folder_window_forward(self):
        self.windows.return_value = [(4242, "trabalhos")]
        plan = self.plan("clicar no ícone da pasta trabalhos na barra de tarefas")
        existing = plan["subtasks"][0]["params"]["existing"]
        self.assertEqual((existing["action"], existing["hwnd"]), ("focus_window", 4242))

    def test_bring_to_front_without_window_opens_the_folder(self):
        self.assertEqual(self.opened(self.plan("traz a pasta trabalhos pra frente")), str(self.trabalhos))

    def test_other_requests_follow_the_normal_flow(self):
        for said in ("criar um site sobre gatos", "abrir o Google", "abrir a pasta trabalhos na Área de Trabalho",
                     "pesquisar receitas no YouTube", "abre o VS Code",
                     "abrir o arquivo do site no VS Code e depois abrir o mesmo no navegador"):
            self.assertIsNone(self.plan(said), said)

    def test_steps_are_checked_again_before_running(self):
        ok = E.existing_steps({"action": "open_path", "path": str(self.project)})
        self.assertEqual(ok[0]["action"], "open_path")
        self.assertEqual(E.existing_steps({"action": "open_path", "path": str(self.project / "nao-existe")}), [])
        exe = self.project / "x.exe"
        exe.write_text("x")
        self.assertEqual(E.existing_steps({"action": "open_path", "path": str(exe)}), [])
        self.assertEqual(E.existing_steps({"action": "run_command", "path": "x"}), [])

    def test_desktop_agent_runs_only_the_checked_steps(self):
        from agents.desktop_agent import DesktopAgent
        agent = DesktopAgent.__new__(DesktopAgent)
        plan = agent.plan({"task": "x", "params": {"existing": {"action": "open_path", "path": str(self.project)}}})
        self.assertEqual([s["action"] for s in plan["steps"]], ["open_path"])
        gone = agent.plan({"task": "x", "params": {"existing": {"action": "open_path", "path": "C:/nao/existe"}}})
        self.assertEqual(gone["steps"], [])
        self.assertIn("error", gone)


class CodeAgentIntent(unittest.TestCase):
    def agent(self):
        from agents.code_agent import CodeAgent
        agent = CodeAgent.__new__(CodeAgent)
        agent.plan_edit = Mock(return_value={"steps": [{"action": "edit_project"}]})
        return agent

    def test_looking_at_a_project_never_creates_or_edits_one(self):
        # Real: "verificar o estado do site" criou um projeto novo; "abrir no navegador" editou arquivos
        agent = self.agent()
        project = {"continue": {"type": "code", "folder": "C:/x"}}
        for said, params in (("verificar o estado atual do site", {}),
                             ("executar o programa do site", project),
                             ("abrir o resultado do site no navegador", project),
                             ("o que falta no site?", project)):
            with patch("agents.artifact_planner.plan_artifact") as create:
                plan = agent.plan({"task": said, "original_task": said, "params": params})
            self.assertEqual(plan["steps"], [], said)
            self.assertIn("Não criei nem alterei nada", plan["error"])
            create.assert_not_called()
        agent.plan_edit.assert_not_called()

    def test_creating_and_changing_still_work(self):
        agent = self.agent()
        with patch("agents.artifact_planner.plan_artifact", return_value={"steps": ["x"]}) as create:
            agent.plan({"task": "criar um site sobre gatos", "params": {}})
        create.assert_called_once()
        agent.plan({"task": "muda a cor do titulo para azul", "params": {"continue": {"type": "code", "folder": "C:/x"}}})
        agent.plan_edit.assert_called_once()


class OversizedSite(unittest.TestCase):
    def test_truncated_answer_asks_for_a_smaller_project_not_the_same_again(self):
        from agents.artifact_planner import plan_artifact
        manifest = {"name": "site", "files": [{"path": "index.html", "content": "<html><body>ok</body></html>"}]}
        client = SimpleNamespace(metrics={"truncated": 0}, prompts=[], efforts=[])

        def message(**kwargs):
            client.prompts.append(kwargs["user_content"])
            client.efforts.append(kwargs["effort"])
            if len(client.prompts) == 1:
                client.metrics = {"truncated": 1}
                return '{"name": "site", "files": [{"path": "index.html", "content": "<html'
            return json.dumps(manifest)
        client.message = message
        agent = SimpleNamespace(name="CODE", effort="high", model="m", _client=client,
                                _extract_task_text=lambda task: task)
        with patch("agents.artifact_planner.brain_guide", return_value=""):
            result = plan_artifact(agent, "criar um site estático bem profissional sobre eleições")
        self.assertEqual(result["steps"][0]["params"]["manifest"]["name"], "site")
        self.assertIn("mais enxuta", client.prompts[1])
        self.assertEqual(client.efforts, ["medium", "low"])     # site estatico nao usa raciocinio alto

    def test_truncated_twice_gives_a_clear_message(self):
        from agents.artifact_planner import plan_artifact
        client = SimpleNamespace(metrics={"truncated": 0})

        def message(**kwargs):
            client.metrics = {"truncated": client.metrics["truncated"] + 1}
            return '{"name": "x", "files": ['
        client.message = message
        agent = SimpleNamespace(name="CODE", effort="high", model="m", _client=client, _extract_task_text=lambda t: t)
        with patch("agents.artifact_planner.brain_guide", return_value=""):
            result = plan_artifact(agent, "criar um site enorme")
        self.assertEqual(result["steps"], [])
        self.assertIn("grande demais", result["error"])


class LocalPagesInTheBrowser(unittest.TestCase):
    def test_local_paths_become_file_urls_only_for_existing_pages(self):
        from core.browser_pilot import local_page_url
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "index.html").write_text("x")
            uri = Path(tmp, "index.html").resolve().as_uri()
            self.assertEqual(local_page_url(tmp), uri)
            self.assertEqual(local_page_url(tmp.replace("\\", "/")), uri)
            # "c/Users/..." do teste real; na CI do GitHub a pasta fica no disco D:, fora de Users
            self.assertEqual(local_page_url(tmp[0] + tmp[2:].replace("\\", "/")), uri)
            self.assertEqual(local_page_url(uri), uri)
            (Path(tmp) / "run.bat").write_text("x")
            self.assertEqual(local_page_url(str(Path(tmp) / "run.bat")), "")
        self.assertEqual(local_page_url("c/Users/nao/existe/x.html"), "")
        self.assertEqual(local_page_url("q/nao/existe.html"), "q/nao/existe.html")   # nao existe: segue como endereco

class FriendlyErrors(unittest.TestCase):
    def test_file_agent_explains_what_it_can_do(self):
        from agents.file_agent import NO_FILE_OPERATION
        self.assertNotIn("LLM", NO_FILE_OPERATION)
        self.assertIn("abre", NO_FILE_OPERATION)


class DryRunLeavesNoTrace(unittest.TestCase):
    def test_simulation_does_not_write_a_plan_to_the_vault(self):
        source = (Path(__file__).resolve().parents[1] / "desktop" / "controller.py").read_text(encoding="utf-8")
        self.assertIn("brain_plan = None if dry_run else self._brain.write_plan(task, plan)", source)
        self.assertIn('if plan.get("rejected_plan") and not dry_run:', source)


if __name__ == "__main__":
    unittest.main()
