---
tipo: tarefa-referencia
agente: CODE
contexto: "python_script"
keywords: gerador code crie script gera link
tags: [referencia, code]
cssclasses: [ref-note]
---
# Gerador de QR code

> [!route] Pedido exemplo
> crie um script que gera qr code de um link

**Agente:** [[Code Agent]] · **Contexto:** python_script

## Caminho
1. qrcode + PIL, salva PNG
2. README

## Forma alternativa
Site com lib JS

## Critério de aceite
PNG gerado

## Armadilha
Dependência externa: listar no requirements

## Subagentes
- [[Architect]] — 1 · Entender
- [[Builder]] — 2 · Montar
- [[Reviewer]] — 3 · Conferir
