---
tipo: tarefa-referencia
agente: FILE
contexto: "archive"
keywords: descompactar arquivo extraia dados zip pasta downloads
tags: [referencia, file]
cssclasses: [ref-note]
---
# Descompactar arquivo

> [!route] Pedido exemplo
> extraia o arquivo dados.zip da pasta downloads

**Agente:** [[File Agent]] · **Contexto:** archive

## Caminho
1. zipfile extractall em Downloads/dados/

## Forma alternativa
—

## Critério de aceite
Arquivos extraídos em pasta própria

## Armadilha
Zip slip: validar caminhos internos

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
