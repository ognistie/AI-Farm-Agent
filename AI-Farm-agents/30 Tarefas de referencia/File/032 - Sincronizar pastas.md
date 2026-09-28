---
tipo: tarefa-referencia
agente: FILE
contexto: "sync"
keywords: sincronizar pastas copie backup arquivos novos pasta projetos
tags: [referencia, file]
cssclasses: [ref-note]
---
# Sincronizar pastas

> [!route] Pedido exemplo
> copie para backup só os arquivos novos da pasta projetos

**Agente:** [[File Agent]] · **Contexto:** sync

## Caminho
1. Comparar mtime/tamanho
2. copiar só novos/alterados
3. resumo

## Forma alternativa
robocopy /E documentado

## Critério de aceite
Backup atualizado

## Armadilha
Nunca apagar do destino sem pedido

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
