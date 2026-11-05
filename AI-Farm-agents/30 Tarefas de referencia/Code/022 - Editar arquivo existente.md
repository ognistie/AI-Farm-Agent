---
tipo: tarefa-referencia
agente: CODE
keywords: editar mudar corrigir refatorar projeto arquivo desfazer
estado: curado
verificado: nao
revisado_em: 2026-10-31
tags: [referencia, code]
cssclasses: [ref-note]
---
# Editar arquivo existente

Procedimento revisado contra o codigo atual. Exige validacao desta versao antes de ser
promovido a caminho comprovado; contagens historicas nao validam um procedimento modificado.

## Caminho
CODE -> read_project do projeto da sessao -> edit_project com files e expected_hashes -> backup e publicacao -> conferir conteudo. revert_project apenas sem conflitos.

## Aceite e limites
- Usar somente a pasta confiavel da sessao; nao aceitar uma pasta arbitraria sugerida pelo modelo.
- Recusar snapshot desatualizado. Rollback em falha detectada; backup preservado.
- Desfazer recusa arquivo alterado pelo usuario ou backup corrompido. Versoes antigas sem hashes exigem recuperacao manual.
