---
tipo: tarefa-referencia
agente: FILE
contexto: "archive"
keywords: compactar arquivos selecionados compacte todas imagens area trabalho zip
tags: [referencia, file]
cssclasses: [ref-note]
---
# Compactar arquivos selecionados

> [!route] Pedido exemplo
> compacte todas as imagens da área de trabalho em um zip

**Agente:** [[File Agent]] · **Contexto:** archive

## Caminho
1. glob imagens → zipfile
2. resumo

## Forma alternativa
—

## Critério de aceite
Zip com as imagens

## Armadilha
Não apagar originais

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
