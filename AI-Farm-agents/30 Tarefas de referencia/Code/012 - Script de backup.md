---
tipo: tarefa-referencia
agente: CODE
contexto: "python_automation"
keywords: script backup crie faz pasta documentos zip
tags: [referencia, code]
cssclasses: [ref-note]
---
# Script de backup

> [!route] Pedido exemplo
> crie um script que faz backup da pasta documentos em zip

**Agente:** [[Code Agent]] · **Contexto:** python_automation

## Caminho
1. shutil.make_archive com data no nome
2. README

## Forma alternativa
FILE Agent faz o backup agora

## Critério de aceite
Script gera zip

## Armadilha
Não apagar backups antigos sem pedido

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
