---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Documento"
keywords: abrir arquivo app padrao abra relatorio pdf area trabalho
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir arquivo com app padrão

> [!route] Pedido exemplo
> abra o arquivo relatorio.pdf da área de trabalho

**Agente:** [[Desktop Agent]] · **Contexto:** Documento

## Caminho
1. run_python os.startfile(Desktop/relatorio.pdf)

## Forma alternativa
FILE find_files se o caminho for incerto

## Critério de aceite
PDF aberto

## Armadilha
Arquivo inexistente: reportar, não criar

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
