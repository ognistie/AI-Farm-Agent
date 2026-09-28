---
tipo: tarefa-referencia
agente: FILE
contexto: "organize"
keywords: organizar projetos codigo organize pasta separando python javascript
tags: [referencia, file]
cssclasses: [ref-note]
---
# Organizar projetos de código

> [!route] Pedido exemplo
> organize minha pasta de projetos separando python e javascript

**Agente:** [[File Agent]] · **Contexto:** organize

## Caminho
1. Detectar linguagem por arquivos (.py/.js/package.json)
2. mover pastas inteiras

## Forma alternativa
Só listar classificação

## Critério de aceite
Projetos separados

## Armadilha
Não quebrar projetos com mistura de linguagens

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
