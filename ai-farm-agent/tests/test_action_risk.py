"""Autorizacao por efeito: classificacao, modos e a porta dentro dos pilotos e do executor."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import action_risk as R

SENSITIVE = {"Enviar": "enviar", "Send": "enviar", "Comprar agora": "comprar", "Adicionar ao carrinho": "comprar",
             "Finalizar compra": "pagar", "Pagar": "pagar", "Excluir": "excluir", "Delete": "excluir",
             "Apagar conversa": "excluir", "Publicar": "publicar", "Postar": "publicar", "Responder a todos": "enviar",
             "Encaminhar": "enviar", "Aceito os termos": "aceitar", "Fazer Pix": "transferir", "Desinstalar": "excluir"}
BENIGN = ["Pesquisar", "Abrir", "Fechar aba", "Próximo", "Início", "Minha Rede", "Imagens", "Salvar",
          "Enviar consulta de pesquisa", "Buscar", "Play", "Configurações", "index.html", "Open in Integrated Browser",
          "Notificações", "Voltar", ""]


class Classification(unittest.TestCase):
    def test_every_sensitive_label_is_caught(self):
        for label, kind in SENSITIVE.items():
            self.assertEqual(R.label_risk(label), kind, label)

    def test_ordinary_labels_pass(self):
        for label in BENIGN:
            self.assertIsNone(R.label_risk(label), label)

    def test_enter_in_a_message_field_is_sending(self):
        self.assertEqual(R.ui_risk("type", "Digite uma mensagem", submit=True), "enviar")
        self.assertEqual(R.ui_risk("press", "Mensagem", key="enter"), "enviar")
        self.assertIsNone(R.ui_risk("type", "Pesquisar", submit=True))
        self.assertIsNone(R.ui_risk("type", "Digite uma mensagem", submit=False))
        self.assertIsNone(R.ui_risk("press", "Mensagem", key="tab"))
        self.assertIsNone(R.ui_risk("scroll", "Enviar"))

    def test_executor_steps(self):
        self.assertEqual(R.step_risk("delete_file", {"path": "x"}), "excluir")
        self.assertEqual(R.step_risk("vision_click", {"description": "botão Enviar"}), "enviar")
        self.assertIsNone(R.step_risk("open_path", {"path": "x"}))

    def test_confirmation_must_be_said_by_the_person(self):
        for said in ("confirmo, envia a mensagem pro João", "pode enviar", "tenho certeza, apaga o arquivo", "autorizo"):
            self.assertTrue(R.confirmed(said), said)
        for said in ("envia a mensagem pro João", "manda um oi", "compra o fone", ""):
            self.assertFalse(R.confirmed(said), said)


class Modes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / "auth.jsonl"

    def rows(self):
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def decide(self, mode, task="envia a mensagem pro João", kind="enviar"):
        return R.authorize(kind, task=task, agent="WEB", action="click", label="Enviar", current=mode, log_path=self.log)

    def test_shadow_never_blocks_and_records_what_it_would_block(self):
        self.assertEqual(self.decide("shadow"), "")
        row = self.rows()[0]
        self.assertEqual((row["decision"], row["kind"], row["requested"], row["confirmed"]), ("would_block", "enviar", True, False))

    def test_enforce_blocks_without_confirmation_and_allows_with_it(self):
        message = self.decide("enforce")
        self.assertIn("confirmo", message)
        self.assertEqual(self.decide("enforce", task="confirmo, envia a mensagem pro João"), "")
        self.assertEqual([r["decision"] for r in self.rows()], ["blocked", "allowed"])

    def test_off_and_harmless_actions_record_nothing(self):
        self.assertEqual(self.decide("off"), "")
        self.assertEqual(R.authorize(None, task="x", agent="WEB", action="click", current="enforce", log_path=self.log), "")
        self.assertFalse(self.log.exists())

    def test_log_keeps_the_button_label_never_what_was_typed(self):
        R.authorize("enviar", task="manda: senha 1234", agent="DESKTOP", action="type", label="Mensagem",
                    current="shadow", log_path=self.log)
        self.assertNotIn("1234", self.log.read_text(encoding="utf-8"))

    def test_report_separates_requested_from_surprise_effects(self):
        self.decide("shadow")
        self.decide("shadow", task="abre o site da loja", kind="comprar")
        out = R.report(self.log)
        self.assertEqual((out["total"], out["would_block"], out["not_requested"]), (2, 2, 1))
        self.assertEqual(out["by_kind"], {"enviar": 1, "comprar": 1})


class InsidePilots(unittest.TestCase):
    """O piloto para ANTES de clicar quando a porta pede confirmacao."""

    def snapshot(self, name):
        element = SimpleNamespace(id=1, role="botao", name=name, elem=object())
        return SimpleNamespace(title="Loja", url="https://loja", elements=[element], main_texts=[], text="",
                               win=SimpleNamespace(handle=7), render=lambda: "JANELA")

    def test_app_pilot_stops_before_clicking_send(self):
        from core import app_pilot as module
        llm = Mock(return_value=json.dumps({"action": "click", "id": 1}))
        gate = Mock(return_value="Antes de enviar preciso da sua confirmação.")
        pilot = module.AppPilot(llm=llm, authorize_ui=gate)
        clicked = Mock()
        with patch.object(module, "window_from_handle", return_value=SimpleNamespace(handle=7)), \
                patch("core.automation._bring_to_front", return_value=True), \
                patch("core.automation._is_front", return_value=True), \
                patch.object(module.B, "snapshot", return_value=self.snapshot("Enviar")), \
                patch.object(module.B, "wrap", return_value=SimpleNamespace(invoke=clicked, click_input=clicked)), \
                patch.object(module, "_view", return_value=("v",)):
            result = pilot.run("mandar a mensagem", 7, "Chat")
        self.assertEqual(result["status"], "ask_user")
        self.assertIn("confirmação", result["result"])
        clicked.assert_not_called()
        gate.assert_called_once_with("enviar", "click", "Enviar")

    def test_app_pilot_clicks_ordinary_buttons_without_asking(self):
        from core import app_pilot as module
        llm = Mock(side_effect=[json.dumps({"action": "click", "id": 1}), json.dumps({"action": "done", "result": "ok"})])
        gate = Mock(return_value="")
        pilot = module.AppPilot(llm=llm, authorize_ui=gate)
        clicked = Mock()
        with patch.object(module, "window_from_handle", return_value=SimpleNamespace(handle=7)), \
                patch("core.automation._bring_to_front", return_value=True), \
                patch("core.automation._is_front", return_value=True), \
                patch.object(module.B, "snapshot", return_value=self.snapshot("Pesquisar")), \
                patch.object(module.B, "wrap", return_value=SimpleNamespace(invoke=clicked, click_input=clicked)), \
                patch.object(module, "_view", return_value=("v",)), patch.object(module, "_changed", return_value=True):
            result = pilot.run("pesquisar", 7, "App")
        self.assertTrue(result["ok"])
        clicked.assert_called_once()
        gate.assert_not_called()

    def test_browser_pilot_stops_before_buying(self):
        from core import browser_pilot as module
        pilot = module.BrowserPilot(llm=Mock(), authorize_ui=Mock(return_value="Antes de comprar preciso da sua confirmação."))
        clicked = Mock()
        snap = self.snapshot("Comprar agora")
        with patch("core.automation._is_front", return_value=True), patch.object(module.B, "_signature", return_value="s"), \
                patch.object(module.B, "wrap", return_value=SimpleNamespace(invoke=clicked, click_input=clicked)):
            with self.assertRaises(R.NeedsConfirmation):
                pilot._act("click", {"id": 1}, snap)
        clicked.assert_not_called()

    def test_pilot_without_gate_behaves_as_before(self):
        from core import app_pilot as module
        self.assertIsNone(module.AppPilot(llm=Mock()).authorize_ui)


class InsideTheExecutor(unittest.TestCase):
    def engine(self, mode):
        from core.automation import AutomationEngine
        engine = AutomationEngine.__new__(AutomationEngine)
        engine.dry_run, engine.current_agent, engine.authorized_task = False, "FILE", "apaga o relatorio velho"
        engine.executed_steps, engine.workspace, engine._fg_before, engine._expect = [], {}, None, None
        engine.should_stop = None
        return engine

    def test_enforce_turns_a_sensitive_step_into_a_question_before_running(self):
        engine = self.engine("enforce")
        handler = Mock(return_value="apagado")
        with patch("core.action_policy.authorize", return_value=""), patch.object(R, "mode", return_value="enforce"), \
                patch.object(R, "_record"), patch.object(type(engine), "_delete_file", handler, create=True):
            result = engine.execute("delete_file", {"path": "C:/x/relatorio.txt"})
        self.assertEqual(result["status"], "needs_confirmation")
        handler.assert_not_called()

    def test_shadow_lets_the_step_run_and_records_it(self):
        engine = self.engine("shadow")
        recorded = []
        with patch("core.action_policy.authorize", return_value=""), patch.object(R, "mode", return_value="shadow"), \
                patch.object(R, "_record", side_effect=lambda row, path=None: recorded.append(row)):
            message = engine._authorize_ui(R.step_risk("delete_file", {"path": "x"}), "delete_file", "")
        self.assertEqual(message, "")
        self.assertEqual(recorded[0]["decision"], "would_block")

    def test_ordinary_steps_never_reach_the_gate(self):
        engine = self.engine("enforce")
        with patch.object(R, "authorize") as gate:
            self.assertEqual(engine._authorize_ui(R.step_risk("open_path", {"path": "x"}), "open_path"), "")
        gate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
