---
tipo: tarefa-referencia
agente: CODE
contexto: "python_data"
keywords: automacao planilha crie script junta varias planilhas excel
tags: [referencia, code]
cssclasses: [ref-note]
---
# Automação de planilha

> [!route] Pedido exemplo
> crie um script que junta várias planilhas excel em uma

**Agente:** [[Code Agent]] · **Contexto:** python_data

## Caminho
1. pandas.concat + openpyxl
2. README

## Forma alternativa
DATA Agent monta a planilha final

## Critério de aceite
Script consolida arquivos

## Armadilha
Colunas diferentes entre arquivos

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
