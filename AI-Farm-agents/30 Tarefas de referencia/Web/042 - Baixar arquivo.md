---
tipo: tarefa-referencia
agente: WEB
contexto: "Download"
keywords: baixar arquivo baixe instalador code
tags: [referencia, web]
cssclasses: [ref-note]
---
# Baixar arquivo

> [!route] Pedido exemplo
> baixe o instalador do vs code

**Agente:** [[Web Agent]] · **Contexto:** Download

## Caminho
1. web_goto code.visualstudio.com/download
2. wait 2 (usuário escolhe a versão)

## Forma alternativa
Winget no terminal (fora do escopo sem pedido)

## Critério de aceite
Página oficial de download aberta

## Armadilha
Download só de fonte oficial; confirmar antes de executar

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
