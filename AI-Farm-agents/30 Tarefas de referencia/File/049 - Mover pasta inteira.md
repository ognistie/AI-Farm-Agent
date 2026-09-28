---
tipo: tarefa-referencia
agente: FILE
contexto: "move"
keywords: mover pasta inteira mova fotos antigas disco
tags: [referencia, file]
cssclasses: [ref-note]
---
# Mover pasta inteira

> [!route] Pedido exemplo
> mova a pasta fotos antigas para o disco d

**Agente:** [[File Agent]] · **Contexto:** move

## Caminho
1. shutil.move com verificação de destino e espaço

## Forma alternativa
Copiar e manter original

## Critério de aceite
Pasta no destino

## Armadilha
Destino já existe: não mesclar sem pedir

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
