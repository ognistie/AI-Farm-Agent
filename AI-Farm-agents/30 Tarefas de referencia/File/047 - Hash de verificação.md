---
tipo: tarefa-referencia
agente: FILE
contexto: "integridade"
keywords: hash verificacao gere sha256 arquivo instalador exe
tags: [referencia, file]
cssclasses: [ref-note]
---
# Hash de verificação

> [!route] Pedido exemplo
> gere o sha256 do arquivo instalador.exe

**Agente:** [[File Agent]] · **Contexto:** integridade

## Caminho
1. hashlib sha256 em blocos
2. exibir

## Forma alternativa
—

## Critério de aceite
Hash exibido

## Armadilha
Arquivo grande: ler em blocos

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
