---
tipo: tarefa-referencia
agente: FILE
contexto: "organize / datas"
keywords: organizar data organize minhas fotos ano mes
tags: [referencia, file]
cssclasses: [ref-note]
---
# Organizar por data

> [!route] Pedido exemplo
> organize minhas fotos por ano e mês

**Agente:** [[File Agent]] · **Contexto:** organize / datas

## Caminho
1. ~/Pictures
2. data EXIF ou modificação
3. pastas AAAA/MM

## Forma alternativa
Só por ano

## Critério de aceite
Fotos em pastas de data

## Armadilha
EXIF ausente: usar data do arquivo

## Subagentes
- [[PathResolver]] — 1 · Entender
- [[OperationPlanner]] — 2 · Montar
- [[SafetyAuditor]] — 3 · Conferir
