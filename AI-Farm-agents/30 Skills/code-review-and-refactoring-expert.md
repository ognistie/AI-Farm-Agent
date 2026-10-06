---
tipo: skill
origem: AIWorkbench
agentes: [CODE]
sempre_para: []
ativa_quando: muda, troca, altera, corrige, conserta, ajusta, melhora, refatora, bug, erro, quebrou, nao funciona, revisa, limpa o codigo, organiza o codigo
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# code-review-and-refactoring-expert

> [!skill] O que faz
> Achar defeitos reais e melhorar a estrutura com escopo apertado, preservando o comportamento.

**Usada por:** [[Code Agent]]

## Quando usar
- Alterar/corrigir um projeto já criado
- Revisar ou limpar código

Ativa sozinha quando o pedido fala de: muda, troca, altera, corrige, conserta, ajusta, melhora, refatora, bug, erro, quebrou, nao funciona, revisa, limpa o codigo, organiza o codigo.

## Como o agente aplica
- **Code Agent:** Na edição de projeto existente: altere SÓ o que foi pedido; preserve estrutura, nomes e o resto do visual.
- **Code Agent:** Antes de mudar, entenda onde o comportamento nasce (CSS vs HTML vs JS) e mude no lugar certo.
- **Code Agent:** Bug: corrija a causa (não o sintoma) e confira que o resto continua funcionando.
- **Code Agent:** Devolva só os arquivos alterados; nada de reformatar o arquivo inteiro.

## Regras
- Não confundir preferência com defeito
- Não misturar refatoração com mudança não pedida
- Mudanças pequenas e verificadas

## Conferir antes de concluir
- Só o pedido mudou
- Nada que funcionava quebrou
- A causa foi corrigida, não escondida

## Fluxo (catálogo)
1. Separar revisão de edição
2. Ler o código, quem chama e os testes
3. Priorizar correção, segurança e confiabilidade
4. Proteger o comportamento antes de refatorar
5. Revisar o resultado final atrás de mudanças acidentais

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/code-review-and-refactoring-expert) · como os agentes usam: [[Skills]]
