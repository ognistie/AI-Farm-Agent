---
tipo: skill
origem: AIWorkbench
agentes: [CODE]
sempre_para: []
ativa_quando: identidade visual, paleta, cores, tema, tema escuro, modo escuro, padronizar, componentes, estilo, fonte, tipografia, consistente
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# design-system-architect

> [!skill] O que faz
> Sistema visual consistente (tokens de cor, tipografia, espaçamento, componentes) sem engessar variações legítimas.

**Usada por:** [[Code Agent]]

## Quando usar
- Trocar cores/tema, criar identidade visual, padronizar estilo

Ativa sozinha quando o pedido fala de: identidade visual, paleta, cores, tema, tema escuro, modo escuro, padronizar, componentes, estilo, fonte, tipografia, consistente.

## Como o agente aplica
- **Code Agent:** Centralize cores, fontes e espaçamentos em variáveis CSS (:root { --cor-primaria: … }) e use só elas.
- **Code Agent:** Ao trocar cor/tema, mude o token — não cada regra solta; mantenha contraste legível (texto sobre fundo).
- **Code Agent:** Modo escuro: redefina os tokens em um bloco próprio, sem duplicar o CSS inteiro.

## Regras
- Não transformar exceção em variante
- Não quebrar quem usa sem migração
- Uma fonte só para os tokens

## Conferir antes de concluir
- Nenhuma cor/fonte 'solta' fora dos tokens
- Contraste legível nos dois temas
- Botões e links com estados (hover, foco, desabilitado)

## Fluxo (catálogo)
1. Auditar decisões repetidas e inconsistências
2. Definir tokens semânticos
3. Especificar anatomia e estados dos componentes
4. Embutir acessibilidade
5. Planejar migração e documentação

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/design-system-architect) · como os agentes usam: [[Skills]]
