---
tipo: tarefa-referencia
agente: FILE
contexto: "convert"
keywords: converter imagens converta png pasta jpg
tags: [referencia, file]
cssclasses: [ref-note]
---
# Converter imagens

> [!route] Pedido exemplo
> converta as imagens png da pasta imagens para jpg

**Agente:** [[File Agent]] · **Contexto:** convert

## Caminho
1. PIL abrir/salvar como .jpg em subpasta 'jpg'
2. manter originais

## Forma alternativa
—

## Critério de aceite
JPGs criados

## Armadilha
Transparência vira fundo branco

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
