---
tipo: tarefa-referencia
agente: CODE
keywords: site html css javascript pagina landing componente tema
estado: curado
verificado: nao
revisado_em: 2026-10-31
tags: [referencia, code]
cssclasses: [ref-note]
---
# Criar site sobre um tema

Procedimento revisado contra o codigo atual. Exige validacao desta versao antes de ser
promovido a caminho comprovado; contagens historicas nao validam um procedimento modificado.

## Caminho
CODE -> create_project(manifest: name, files[path, content]) -> diretorio novo -> conferencia de hashes. Nao executar nem abrir automaticamente.

## Aceite e limites
- HTML semantico, CSS responsivo e estados de foco conforme o pedido; JS apenas quando necessario.
- Incluir todos os arquivos referenciados. Ate 40 arquivos e 1 MiB; sem caminhos absolutos.
- Hash e sintaxe comprovam gravacao, nao comportamento visual ou funcional. Revisao no navegador e uma etapa separada.
