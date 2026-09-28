---
tipo: tarefa-referencia
agente: DATA
contexto: "alunos"
keywords: boletim escolar crie notas media alunos
tags: [referencia, data]
cssclasses: [ref-note]
---
# Boletim escolar

> [!route] Pedido exemplo
> crie um boletim com notas e média dos alunos

**Agente:** [[Data Agent]] · **Contexto:** alunos

## Caminho
1. Notas 1–3, Média (=AVERAGE), Situação (=IF(Média>=6;...))

## Forma alternativa
Gráfico de médias

## Critério de aceite
Situação correta por aluno

## Armadilha
Critério de aprovação: perguntar ou usar 6 e avisar

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
