---
tipo: tarefa-referencia
agente: DESKTOP
contexto: "Documento formal"
keywords: escrever carta word abra escreva agradecimento cliente
tags: [referencia, desktop]
cssclasses: [ref-note]
---
# Escrever carta no Word

> [!route] Pedido exemplo
> abra o word e escreva uma carta de agradecimento ao cliente

**Agente:** [[Desktop Agent]] · **Contexto:** Documento formal

## Caminho
1. Maestro gera carta
2. rotina Word
3. type_text

## Forma alternativa
DATA/CODE gerando .docx com python-docx

## Critério de aceite
Carta completa no documento

## Armadilha
Sem nome do cliente: usar genérico e avisar

## Subagentes
- [[AppResolver]] — 1 · Entender
- [[ContentComposer]] — 2 · Montar
- [[ScreenGuard]] — 3 · Conferir
