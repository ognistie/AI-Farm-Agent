---
tipo: tarefa-referencia
agente: CODE
contexto: "automation / windows"
keywords: script powershell crie lista programas instalados
tags: [referencia, code]
cssclasses: [ref-note]
---
# Script PowerShell

> [!route] Pedido exemplo
> crie um script powershell que lista programas instalados

**Agente:** [[Code Agent]] · **Contexto:** automation / windows

## Caminho
1. Script .ps1 read-only + README

## Forma alternativa
Python com winreg

## Critério de aceite
Lista gerada

## Armadilha
Scripts de sistema: só leitura sem pedido

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
