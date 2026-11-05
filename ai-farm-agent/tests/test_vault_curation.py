import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.brain import Brain
from core.memory_gate import REFS, restore_references, verify_all, record_outcome
from core.vault_curation import load_retirements, review_deletions


class CurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'AI-Farm-agents'
        self.canonical = self.vault / REFS / 'Nova.md'
        self.canonical.parent.mkdir(parents=True)
        self.canonical.write_text('---\ntipo: tarefa-referencia\nagente: CODE\nverificado: nao\n---\n# Nova\n', encoding='utf-8')
        self.old = '---\ntipo: tarefa-referencia\nagente: CODE\nverificado: sim\nkeywords: criar site\n---\n# Criar site\n\n## Caminho\nrun_python\n'
        self.digest = hashlib.sha256(self.old.encode()).hexdigest()
        self.path = 'AI-Farm-agents/' + REFS + '/Antiga.md'
        self.manifest = self.root / 'docs/research/vault-curation.json'
        self.manifest.parent.mkdir(parents=True)
        self.data = {'schema': 1, 'retired': [{'path': self.path, 'source_sha256': self.digest,
            'decision': 'consolidated', 'replacement': 'AI-Farm-agents/' + REFS + '/Nova.md',
            'reason': 'Receita antiga consolidada em procedimento com contrato atual.'}]}
        self.save()
        self.archive = self.root / 'archive'; self.archive.mkdir()
        (self.archive / 'Antiga.md').write_text(self.old, encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding='utf-8')

    def test_only_exact_reviewed_deletion_is_accepted(self):
        self.assertEqual(review_deletions(self.vault, {self.path: self.digest})['pending'], [])
        self.assertEqual(review_deletions(self.vault, {self.path: 'wrong'})['pending'], [self.path])
        other = 'AI-Farm-agents/Outra.md'
        self.assertEqual(review_deletions(self.vault, {other: self.digest})['pending'], [other])

    def test_archived_retired_note_never_returns_or_learns(self):
        self.assertEqual(restore_references(self.vault, self.archive), [])
        report = verify_all(self.vault, self.root / 'missing-history', apply=True, archive=self.archive)
        self.assertEqual(report['restauradas'], [])
        entry = {'task': 'criar site', 'success': True, 'subtasks': [{'agent': 'CODE'}],
                 'reference_evidence': [{'note': 'Antiga.md', 'verified': True, 'verifier': 'human'}]}
        self.assertIsNone(record_outcome(self.vault, entry, self.archive))
        self.assertFalse((self.vault / REFS / 'Antiga.md').exists())

    def test_missing_replacement_and_reappearing_source_fail_closed(self):
        self.canonical.unlink()
        with self.assertRaises(ValueError): load_retirements(self.vault)
        self.canonical.write_text('# Nova')
        (self.vault / REFS / 'Antiga.md').write_text(self.old)
        with self.assertRaises(ValueError): restore_references(self.vault, self.archive)

    def test_invalid_manifest_does_not_restore_archive(self):
        self.manifest.write_text('{broken')
        with self.assertRaises(ValueError): restore_references(self.vault, self.archive)
        self.assertFalse((self.vault / REFS / 'Antiga.md').exists())

    def test_planned_playbook_is_excluded_before_model_context(self):
        folder = self.vault / '10 Agentes/Code'; folder.mkdir(parents=True)
        for state in ('planejado', 'experimental', 'retirado', 'curado'):
            (folder / (state + '.md')).write_text(
                f'---\ntipo: playbook\nagente: CODE\nestado: {state}\nkeywords: criar site\n---\n\n## Caminho\ncreate_project\n', encoding='utf-8')
        refs = Brain(str(self.vault)).find_references('criar site', k=10, agent='CODE')
        self.assertEqual([r['title'] for r in refs], ['curado'])

    def test_link_audit_distinguishes_markdown_from_base_view(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
        from check_vault import audit
        (self.vault / 'Skills.md').write_text('# Skills')
        (self.vault / 'Skills.base').write_text('views: []')
        (self.vault / 'Inicio.md').write_text('[[Skills]] ![[Skills.base]]')
        # This fixture has no canonical acceptance section; inspect link errors only.
        self.assertFalse(any('link' in error for error in audit(self.vault)['errors']))

    def test_link_audit_reports_missing_target(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
        from check_vault import audit
        (self.vault / 'Inicio.md').write_text('[[Procedimento ausente]]')
        self.assertTrue(any('Procedimento ausente' in error for error in audit(self.vault)['errors']))

    def test_query_coverage_survives_consolidation_without_generic_false_hit(self):
        folder = self.vault / '10 Agentes/Data'; folder.mkdir(parents=True)
        (folder / 'Cadastro.md').write_text(
            '---\ntipo: playbook\nagente: DATA\nestado: curado\n'
            'keywords: lista cadastro contatos clientes estoque tabela planilha controle vendas fornecedores produtos campos\n'
            '---\n\n## Caminho\ncreate_workbook\n', encoding='utf-8')
        brain = Brain(str(self.vault))
        self.assertEqual(brain.find_references('crie uma planilha de controle de estoque', agent='DATA')[0]['title'], 'Cadastro')
        self.assertEqual(brain.find_references('planilha de astrofisica desconhecida', agent='DATA'), [])
        self.assertEqual(brain.find_references('planilha controle estoque', agent='FILE'), [])

    def test_resurfaced_retired_content_is_excluded_before_retrieval(self):
        (self.vault / REFS / 'Antiga.md').write_text(self.old, encoding='utf-8')
        self.assertEqual(Brain(str(self.vault)).find_references('criar site', agent='CODE'), [])


if __name__ == '__main__': unittest.main()
