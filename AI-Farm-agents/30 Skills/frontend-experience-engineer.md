---
tipo: skill
origem: AIWorkbench
agentes: [CODE]
sempre_para: []
ativa_quando: site, pagina, html, css, javascript, landing, formulario, botao, menu, responsivo, celular, interativo, jogo, calculadora, quiz, dashboard
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# frontend-experience-engineer

> [!skill] O que faz
> Interface que funciona em qualquer tela, com teclado e mouse, e em todos os estados (carregando, vazio, erro, sucesso).

**Usada por:** [[Code Agent]]

## Quando usar
- Sites, páginas, formulários, jogos e interfaces em HTML/CSS/JS

Ativa sozinha quando o pedido fala de: site, pagina, html, css, javascript, landing, formulario, botao, menu, responsivo, celular, interativo, jogo, calculadora, quiz, dashboard.

## Como o agente aplica
- **Code Agent:** HTML semântico (header, nav, main, section, footer, button) e todo controle utilizável por teclado (foco visível).
- **Code Agent:** Responsivo de verdade: layout em grid/flex, media query para celular (~600px), imagens com max-width:100%.
- **Code Agent:** Formulários com label, validação e mensagem de erro visível ao lado do campo.
- **Code Agent:** JS: trate o estado vazio e o erro (ex.: lista vazia, entrada inválida) — nunca deixe a tela quebrada.

## Regras
- Não criar interação só de mouse
- Não esconder erro atrás de 'carregando'
- Não otimizar sem evidência

## Conferir antes de concluir
- Funciona no celular e no desktop
- Dá para usar só com teclado
- Erros aparecem para o usuário

## Fluxo (catálogo)
1. Inspecionar componentes e estilos
2. Modelar estados: carregando, vazio, erro, sucesso
3. Interação semântica e completa por teclado
4. Adaptar a telas, conteúdo, tema e movimento
5. Verificar visual e automaticamente

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/frontend-experience-engineer) · como os agentes usam: [[Skills]]
