---
tipo: tarefa-referencia
agente: FILE
contexto: "delete confirmado"
keywords: limpar pasta temporaria limpe arquivos tmp area trabalho confirmo
tags: [referencia, file]
cssclasses: [ref-note]
---
# Limpar pasta temporária

> [!route] Pedido exemplo
> limpe os arquivos .tmp da área de trabalho, confirmo

**Agente:** [[File Agent]] · **Contexto:** delete confirmado

## Caminho
1. glob *.tmp em Desktop
2. send2trash
3. resumo

## Forma alternativa
—

## Critério de aceite
Temporários na lixeira

## Armadilha
Filtrar só a extensão pedida

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
