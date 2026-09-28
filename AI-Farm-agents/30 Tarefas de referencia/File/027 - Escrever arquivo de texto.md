---
tipo: tarefa-referencia
agente: FILE
contexto: "write"
keywords: escrever arquivo texto crie tarefas txt area trabalho minhas hoje
tags: [referencia, file]
cssclasses: [ref-note]
---
# Escrever arquivo de texto

> [!route] Pedido exemplo
> crie um arquivo tarefas.txt na área de trabalho com minhas tarefas de hoje

**Agente:** [[File Agent]] · **Contexto:** write

## Caminho
1. Maestro gera conteúdo
2. write_file Desktop/tarefas.txt
3. não sobrescrever

## Forma alternativa
DESKTOP Bloco de Notas

## Critério de aceite
Arquivo criado

## Armadilha
Arquivo já existe: sufixo

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
