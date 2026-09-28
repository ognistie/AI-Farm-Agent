---
tipo: tarefa-referencia
agente: FILE
contexto: "cadeia WEB → FILE"
keywords: arquivos compartilhados outro agente salve resultado pesquisa arquivo txt
tags: [referencia, file]
cssclasses: [ref-note]
---
# Arquivos compartilhados com outro agente

> [!route] Pedido exemplo
> salve o resultado da pesquisa em um arquivo txt

**Agente:** [[File Agent]] · **Contexto:** cadeia WEB → FILE

## Caminho
1. Usar {output_text_N}
2. write_file Desktop/pesquisa_<tema>.txt

## Forma alternativa
DESKTOP Bloco de Notas

## Critério de aceite
Arquivo com o texto lido

## Armadilha
Não inventar conteúdo

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
