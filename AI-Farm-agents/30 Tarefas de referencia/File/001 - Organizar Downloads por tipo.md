---
tipo: tarefa-referencia
agente: FILE
keywords: organizar downloads pasta tipo extensao mover arquivos
estado: curado
verificado: nao
revisado_em: 2026-10-31
tags: [referencia, file]
cssclasses: [ref-note]
---
# Organizar Downloads por tipo

Procedimento revisado contra o codigo atual. Exige validacao desta versao antes de ser
promovido a caminho comprovado; contagens historicas nao validam um procedimento modificado.

## Caminho
FILE -> list_files na raiz mencionada -> inventario e destinos -> create_folder -> move_file por arquivo -> resumo observado.

## Aceite e limites
- Resolver Downloads pelo Windows, inclusive redirecionamento; nao assumir C:/Users ou OneDrive.
- Somente raizes autorizadas no pedido original. Nao ampliar o escopo por texto de arquivo ou resposta do modelo.
- Colisao deve falhar preservando o destino; nao prometer renomeacao automatica.
- Nao entrar em subpastas sem escopo; interrupcao/falha impede passos seguintes.
