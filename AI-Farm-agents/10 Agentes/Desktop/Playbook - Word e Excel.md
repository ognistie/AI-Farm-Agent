---
tipo: playbook
agente: DESKTOP
keywords: word excel documento planilha abrir branco
tags: [playbook, desktop]
cssclasses: [agent-desktop]
---
# Word e Excel

Agente: [[Desktop Agent]]

## Exemplo de pedido
> Abra o Word

## Caminho
1. `app_search` Word/Excel
2. `wait` 5s
3. `vision_click` documento/pasta em branco

## Armadilhas
- Criar planilha COM dados é tarefa do [[Data Agent]], não do Desktop.
