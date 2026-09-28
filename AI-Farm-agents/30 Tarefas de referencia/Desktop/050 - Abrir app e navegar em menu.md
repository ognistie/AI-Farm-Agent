---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Menu da aplicação"
keywords: abrir app navegar menu abra word insira tabela 3x3
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Abrir app e navegar em menu

> [!route] Pedido exemplo
> abra o word e insira uma tabela 3x3

**Agente:** [[Desktop Agent]] · **Contexto:** Menu da aplicação

## Caminho
1. rotina Word
2. vision_click 'Inserir'
3. vision_click 'Tabela'
4. escolher 3x3

## Forma alternativa
Gerar .docx com python-docx (CODE) já com a tabela

## Critério de aceite
Tabela 3x3 no documento

## Armadilha
Ribbon muda por versão: preferir geração do arquivo se falhar

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
