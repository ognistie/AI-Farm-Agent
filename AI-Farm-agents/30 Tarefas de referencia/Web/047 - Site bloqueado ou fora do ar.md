---
tipo: tarefa-referencia
agente: WEB
contexto: "Falha de rede"
keywords: site bloqueado fora abra
tags: [referencia, web]
cssclasses: [ref-note]
---
# Site bloqueado ou fora do ar

> [!route] Pedido exemplo
> abra o site x.com.br

**Agente:** [[Web Agent]] · **Contexto:** Falha de rede

## Caminho
1. web_goto
2. wait
3. web_read mostra erro → reportar falha literal

## Forma alternativa
Busca pelo nome para achar domínio correto

## Critério de aceite
Erro reportado com mensagem

## Armadilha
Não repetir mais de 3 vezes (circuit-breaker)

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
