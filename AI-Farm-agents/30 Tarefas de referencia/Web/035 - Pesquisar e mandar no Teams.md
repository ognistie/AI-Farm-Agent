---
tipo: tarefa-referencia
agente: WEB
contexto: "Web → Desktop"
keywords: pesquisar mandar teams pesquise cotacao euro mande ana
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisar e mandar no Teams

> [!route] Pedido exemplo
> pesquise a cotação do euro e mande para a ana no teams

**Agente:** [[Web Agent]] · **Contexto:** Web → Desktop

## Caminho
1. 1) WEB busca + web_read 2) DESKTOP teams message={output_summary_1} depends_on=1

## Forma alternativa
Mandar só o link da busca

## Critério de aceite
Mensagem com o valor lido enviada

## Armadilha
Mensagem nunca inventada

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
