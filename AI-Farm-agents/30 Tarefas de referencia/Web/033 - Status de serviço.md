---
tipo: tarefa-referencia
agente: WEB
contexto: "Diagnóstico"
keywords: status servico verifique whatsapp esta fora
tags: [referencia, web]
cssclasses: [ref-note]
---
# Status de serviço

> [!route] Pedido exemplo
> verifique se o whatsapp está fora do ar

**Agente:** [[Web Agent]] · **Contexto:** Diagnóstico

## Caminho
1. Query 'whatsapp fora do ar hoje'
2. web_goto
3. web_read

## Forma alternativa
downdetector.com.br

## Critério de aceite
Status lido

## Armadilha
Não concluir sem evidência da página

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
