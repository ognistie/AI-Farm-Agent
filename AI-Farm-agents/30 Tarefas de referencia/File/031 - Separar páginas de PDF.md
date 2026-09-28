---
tipo: tarefa-referencia
agente: FILE
contexto: "split"
keywords: separar paginas pdf separe pagina arquivo relatorio
tags: [referencia, file]
cssclasses: [ref-note]
---
# Separar páginas de PDF

> [!route] Pedido exemplo
> separe a página 3 do arquivo relatorio.pdf

**Agente:** [[File Agent]] · **Contexto:** split

## Caminho
1. pypdf extrair página 3 → relatorio_p3.pdf

## Forma alternativa
—

## Critério de aceite
Arquivo com a página

## Armadilha
Índice começa em 0 no código

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
