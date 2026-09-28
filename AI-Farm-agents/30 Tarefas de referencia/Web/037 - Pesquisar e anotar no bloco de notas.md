---
tipo: tarefa-referencia
agente: WEB
contexto: "Web → Desktop"
keywords: pesquisar anotar bloco notas pesquise dicas produtividade anote
tags: [referencia, web]
cssclasses: [ref-note]
---
# Pesquisar e anotar no bloco de notas

> [!route] Pedido exemplo
> pesquise dicas de produtividade e anote no bloco de notas

**Agente:** [[Web Agent]] · **Contexto:** Web → Desktop

## Caminho
1. 1) WEB busca + web_read 2) DESKTOP notepad text={output_summary_1}

## Forma alternativa
Maestro escreve resumo próprio com base na leitura

## Critério de aceite
Notas digitadas

## Armadilha
Não colar HTML/lixo da página

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
