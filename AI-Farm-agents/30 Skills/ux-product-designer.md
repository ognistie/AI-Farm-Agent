---
tipo: skill
origem: AIWorkbench
agentes: [DESKTOP, DATA, CODE]
sempre_para: [DESKTOP]
ativa_quando: planilha, tabela, cadastro, formulario, controle, organizar, lista, agenda, relatorio, facil, simples, usuario
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# ux-product-designer

> [!skill] O que faz
> Tornar as tarefas importantes do usuário compreensíveis, eficientes e recuperáveis.

**Usada por:** [[Desktop Agent]] · [[Data Agent]] · [[Code Agent]]

## Quando usar
- Ações em apps abertos
- Planilhas e formulários para o usuário preencher

Ativa sozinha quando o pedido fala de: planilha, tabela, cadastro, formulario, controle, organizar, lista, agenda, relatorio, facil, simples, usuario. Sempre ativa para: Desktop Agent.

## Como o agente aplica
- **Desktop Agent:** Trabalhe na janela que o usuário está usando e não roube o foco à toa; nunca altere o documento dele sem pedido.
- **Desktop Agent:** Se algo bloquear (janela fechada, diálogo inesperado, login), pare e diga exatamente o que falta — não chute.
- **Desktop Agent:** Prefira o caminho que o usuário reconheceria (menu/atalho padrão) e deixe o resultado visível na tela.
- **Data Agent:** Planilha que se usa sozinha: cabeçalho claro, colunas na ordem de leitura, formatos (R$, data, %) e totais visíveis.
- **Data Agent:** Congele a linha de cabeçalho e ajuste largura de coluna; deixe espaço para o usuário continuar preenchendo.
- **Code Agent:** Fluxos curtos: uma ação principal por tela; mensagens de sucesso e de erro em linguagem simples.
- **Code Agent:** Antes de ação destrutiva (apagar, limpar), confirmação clara com a consequência.

## Regras
- Preferência não é evidência
- Não esconder consequências em texto secundário
- Não otimizar só o caminho feliz

## Conferir antes de concluir
- O usuário entende o resultado sem explicação
- Erros dizem como resolver
- Nada do usuário foi alterado sem pedido

## Fluxo (catálogo)
1. Entender usuário, tarefa e riscos
2. Mapear o caminho atual e onde quebra
3. Desenhar o menor fluxo coerente
4. Especificar conteúdo, feedback, permissões e erros
5. Testar as suposições arriscadas

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/ux-product-designer) · como os agentes usam: [[Skills]]
