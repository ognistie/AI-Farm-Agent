import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.brain import Brain


class NoteCache(unittest.TestCase):
    def test_rewrite_with_the_same_timestamp_is_not_served_from_cache(self):
        # Visto no smoke: a nota rebaixada para "verificado: nao" ainda saia como "sim"
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "nota.md"
            note.write_text("verificado: sim", encoding="utf-8")
            stamp = os.stat(note).st_mtime_ns
            brain = Brain(tmp)
            self.assertEqual(brain._read("nota.md"), "verificado: sim")
            note.write_text("verificado: nao", encoding="utf-8")       # mesmo tamanho
            os.utime(note, ns=(stamp, stamp))                          # mesma data, como no passo do relogio
            self.assertEqual(brain._read("nota.md"), "verificado: nao")

    def test_old_unchanged_note_comes_from_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "nota.md"
            note.write_text("conteudo", encoding="utf-8")
            old = time.time() - 60
            os.utime(note, (old, old))
            brain = Brain(tmp)
            self.assertEqual(brain._read("nota.md"), "conteudo")
            stamp = os.stat(note).st_mtime_ns
            note.write_bytes(b"conteudo")                               # outra fonte nao mudaria nada
            os.utime(note, ns=(stamp, stamp))
            brain._cache["nota.md"] = (brain._cache["nota.md"][0], "do cache")
            self.assertEqual(brain._read("nota.md"), "do cache")


if __name__ == "__main__":
    unittest.main()
