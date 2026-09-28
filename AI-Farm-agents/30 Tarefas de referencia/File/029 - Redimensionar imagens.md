---
tipo: tarefa-referencia
agente: FILE
contexto: "convert"
keywords: redimensionar imagens reduza tamanho fotos pasta viagem enviar email
tags: [referencia, file]
cssclasses: [ref-note]
---
# Redimensionar imagens

> [!route] Pedido exemplo
> reduza o tamanho das fotos da pasta viagem para enviar por email

**Agente:** [[File Agent]] · **Contexto:** convert

## Caminho
1. PIL thumbnail 1600px → subpasta 'reduzidas'

## Forma alternativa
Zip das reduzidas

## Critério de aceite
Fotos menores em nova pasta

## Armadilha
Não sobrescrever originais

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
