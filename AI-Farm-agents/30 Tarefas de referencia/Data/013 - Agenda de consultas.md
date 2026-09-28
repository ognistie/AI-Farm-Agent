---
tipo: tarefa-referencia
agente: DATA
contexto: "agendamento"
keywords: agenda consultas crie clinica
tags: [referencia, data]
cssclasses: [ref-note]
---
# Agenda de consultas

> [!route] Pedido exemplo
> crie uma agenda de consultas para clínica

**Agente:** [[Data Agent]] · **Contexto:** agendamento

## Caminho
1. Data, Horário, Paciente, Serviço, Profissional, Status
2. validação de lista

## Forma alternativa
Uma aba por profissional

## Critério de aceite
Agenda filtrável

## Armadilha
Conflito de horário: destacar

## Subagentes
- [[SchemaDesigner]] — 1 · Entender
- [[FormulaChartDesigner]] — 2 · Montar
- [[SheetReviewer]] — 3 · Conferir
