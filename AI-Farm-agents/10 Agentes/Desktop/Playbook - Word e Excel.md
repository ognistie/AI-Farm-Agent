---
tipo: playbook
agente: DESKTOP
keywords: word excel documento planilha abrir branco preencher celula linha coluna
tags: [playbook, desktop]
cssclasses: [agent-desktop]
---
# Word e Excel

Agente: [[Desktop Agent]]

## Exemplo de pedido
> Abra o Word

## Caminho
1. Rotina abre pelo executável (`excel` / `winword`) e espera a janela pelo título
2. Pedido só de abrir: pronto (se já estava aberto na conversa, só traz pra frente)
3. Pedido com conteúdo: `app_task(goal)` na **mesma** janela — na tela inicial escolhe *Pasta de trabalho/Documento em branco*; no Excel vai para A1 (Ctrl+Home) e digita com **Tab** entre colunas e **Enter** para a linha de baixo

## Armadilhas
- Criar planilha COM dados calculados/gráfico é tarefa do [[Data Agent]] (gera o .xlsx pronto), não do Desktop.
- App já aberto na conversa: continuar na mesma pasta de trabalho, nunca abrir outra (a não ser que o usuário diga "outra").
- Atalhos do Office mudam com o idioma (Ctrl+N = negrito em português): preferir botão/menu ([[Atalhos de teclado]]).

