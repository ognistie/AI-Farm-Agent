---
tipo: tarefa-referencia
agente: WEB
contexto: "Formulário"
keywords: formulario web abra contato site empresa
tags: [referencia, web]
cssclasses: [ref-note]
---
# Formulário web

> [!route] Pedido exemplo
> abra o formulário de contato do site da empresa x

**Agente:** [[Web Agent]] · **Contexto:** Formulário

## Caminho
1. Busca + primeiro resultado
2. web_read para achar o link 'Contato'
3. web_click

## Forma alternativa
Pedir a URL ao usuário

## Critério de aceite
Formulário aberto

## Armadilha
Não enviar formulário sem confirmação

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
