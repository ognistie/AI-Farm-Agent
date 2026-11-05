import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop.voice import VoiceController


class ExchangeTests(unittest.TestCase):
    def voice(self):
        voice=VoiceController.__new__(VoiceController)
        voice.live=True
        voice._expect_reply=True
        voice._reply_task=('abrir calculadora','abre a calculadora')
        voice._inflight=True
        voice._say=Mock()
        voice._finish=Mock()
        return voice

    def test_fast_reply_before_finished_is_delivered_once(self):
        v=self.voice()
        reply={'said':'abrir calculadora','text':'A calculadora esta aberta.','speak':False}
        v._on_assistant(reply)
        v._on_done({})
        v._on_assistant(reply)
        v._say.assert_called_once_with(reply['text'],purpose='reply')
        self.assertFalse(v._expect_reply)

    def test_finished_before_reply_does_not_lose_reply(self):
        v=self.voice();v._on_done({})
        v._on_assistant({'said':'abre a calculadora','text':'Concluido.','speak':True})
        v._say.assert_called_once()

    def test_other_task_and_cancelled_reply_are_not_spoken(self):
        v=self.voice()
        v._on_assistant({'said':'outro pedido','text':'resposta antiga','speak':True})
        v._say.assert_not_called()

    def test_same_words_from_old_run_or_other_session_are_rejected(self):
        v=self.voice();v._reply_run_id=2;v._reply_session_id='current'
        for run,session in ((1,'current'),(2,'old')):
            v._on_assistant({'said':'abrir calculadora','text':'antiga','speak':True,'run_id':run,'session_id':session})
        v._say.assert_not_called()
        v._on_assistant({'said':'abrir calculadora','text':'atual','speak':True,'run_id':2,'session_id':'current'})
        v._say.assert_called_once()
        v._expect_reply=False
        v._say.reset_mock()
        v._on_assistant({'said':'abrir calculadora','text':'atrasada','speak':True})
        v._say.assert_not_called()
