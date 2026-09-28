---
tipo: tarefa-referencia
agente: FILE
contexto: "delete confirmado"
keywords: mover lixeira mande arquivo velho docx pode apagar
tags: [referencia, file]
cssclasses: [ref-note]
---
# Mover para lixeira

> [!route] Pedido exemplo
> mande o arquivo velho.docx para a lixeira, pode apagar

**Agente:** [[File Agent]] · **Contexto:** delete confirmado

## Caminho
1. send2trash Desktop/velho.docx

## Forma alternativa
—

## Critério de aceite
Arquivo na lixeira

## Armadilha
Lixeira é reversível: preferir

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
