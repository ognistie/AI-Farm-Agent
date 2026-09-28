---
tipo: tarefa-referencia
agente: FILE
contexto: "move"
keywords: organizar extensao especifica mova todos pdfs pasta downloads documentos
tags: [referencia, file]
cssclasses: [ref-note]
---
# Organizar por extensão específica

> [!route] Pedido exemplo
> mova todos os pdfs da pasta downloads para documentos

**Agente:** [[File Agent]] · **Contexto:** move

## Caminho
1. PathResolver: Downloads, Documents
2. glob *.pdf
3. move com renome em conflito

## Forma alternativa
Copiar em vez de mover

## Critério de aceite
PDFs em Documentos

## Armadilha
Nomes repetidos: sufixo _2

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
