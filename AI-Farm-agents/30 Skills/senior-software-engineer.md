---
tipo: skill
origem: AIWorkbench
agentes: [CODE, DATA, FILE]
sempre_para: [CODE, DATA, FILE]
ativa_quando: script, programa, codigo, automacao, funcao, python, calcular, gerar, converter, processar
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# senior-software-engineer

> [!skill] O que faz
> Entregar a menor implementação coerente que faz o que foi pedido, com validação, erros explícitos e verificação.

**Usada por:** [[Code Agent]] · [[Data Agent]] · [[File Agent]]

## Quando usar
- Qualquer criação de código, script ou automação
- Planilhas geradas por script
- Operações em arquivos

Ativa sozinha quando o pedido fala de: script, programa, codigo, automacao, funcao, python, calcular, gerar, converter, processar. Sempre ativa para: Code Agent, Data Agent, File Agent.

## Como o agente aplica
- **Code Agent:** Código completo e executável: nada de TODO, placeholder ou 'lorem ipsum'.
- **Code Agent:** Trate entradas e erros com mensagem clara (arquivo inexistente, campo vazio, número inválido).
- **Code Agent:** Imprima no fim um resumo verificável do que foi feito (arquivos criados, caminho, contagem).
- **Data Agent:** Script openpyxl completo; valide os dados antes de gravar (tipos, colunas, linhas vazias).
- **Data Agent:** Imprima onde salvou e quantas linhas/colunas; nunca sobrescreva planilha existente sem pedido.
- **File Agent:** Mostre o plano (o que vai mover/renomear) antes de agir em lote.
- **File Agent:** Conflito de nome: renomeie com sufixo; nunca sobrescreva. Imprima o resumo final.

## Regras
- Nunca esconder falhas, segredos ou efeitos destrutivos
- Não mexer no que não foi pedido
- Não dizer que funcionou sem ter conferido

## Conferir antes de concluir
- O pedido inteiro foi atendido (não só a primeira parte)
- Erros previsíveis têm mensagem clara
- O resumo final bate com o que foi feito

## Fluxo (catálogo)
1. Ler instruções, código, testes e configuração
2. Achar invariantes, bordas e falhas
3. Escolher a menor mudança coerente
4. Validar entradas, erros explícitos, observabilidade
5. Rodar checagens proporcionais e revisar o resultado

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/senior-software-engineer) · como os agentes usam: [[Skills]]
