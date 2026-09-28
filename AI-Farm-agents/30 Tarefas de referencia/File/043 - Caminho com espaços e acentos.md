---
tipo: tarefa-referencia
agente: FILE
contexto: "robustez"
keywords: caminho espacos acentos copie pasta relatorios finais backup
tags: [referencia, file]
cssclasses: [ref-note]
---
# Caminho com espaços e acentos

> [!route] Pedido exemplo
> copie a pasta 'Relatórios Finais' para o backup

**Agente:** [[File Agent]] · **Contexto:** robustez

## Caminho
1. pathlib com caminhos entre aspas
2. copytree

## Forma alternativa
—

## Critério de aceite
Cópia correta

## Armadilha
Encoding de acentos no Windows

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
