---
tipo: tarefa-referencia
agente: FILE
contexto: "search"
keywords: encontrar arquivo nome encontre contrato pdf computador
tags: [referencia, file]
cssclasses: [ref-note]
---
# Encontrar arquivo por nome

> [!route] Pedido exemplo
> encontre o arquivo contrato.pdf no meu computador

**Agente:** [[File Agent]] · **Contexto:** search

## Caminho
1. Buscar em pastas do usuário (Desktop, Documents, Downloads) → listar caminhos

## Forma alternativa
Busca em todo C:/Users/<eu>

## Critério de aceite
Caminho(s) listado(s)

## Armadilha
Não varrer C:/Windows

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
