---
tipo: skill
origem: AIWorkbench
agentes: [CODE, MEMORY, MAESTRO]
sempre_para: []
ativa_quando: teste, testes, testar, validar, avaliar, conferir, verifica, garante, qualidade, benchmark
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# ai-evaluation-engineer

> [!skill] O que faz
> Tornar a qualidade mensurável e reprodutível: sucesso observável, casos adversariais, graders e variância.

**Usada por:** [[Code Agent]] · [[Memory Agent]] · [[Maestro]]

## Quando usar
- Pedidos que mencionam testar, validar ou garantir

Ativa sozinha quando o pedido fala de: teste, testes, testar, validar, avaliar, conferir, verifica, garante, qualidade, benchmark.

## Como o agente aplica
- **Code Agent:** Pedido com testes: escreva testes que falham sem a funcionalidade (incluindo caso de borda) e rode-os.
- **Code Agent:** Diga o resultado real dos testes (passou/falhou), nunca presuma.
- **Maestro:** Inclua um passo de conferência quando o pedido pede garantia (ler de volta, abrir o resultado).

## Regras
- Não ajustar em casos reservados
- Não mover a régua depois do resultado
- Registrar modelo, ferramentas e orçamento

## Conferir antes de concluir
- Teste roda e o resultado foi dito como é
- Há pelo menos um caso de borda

## Fluxo (catálogo)
1. Definir sucesso observável e falhas inaceitáveis
2. Criar casos representativos e adversariais antes de ajustar
3. Escolher graders (código, modelo, humano)
4. Rodar várias vezes o que varia
5. Inspecionar traços e resultados

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/ai-evaluation-engineer) · como os agentes usam: [[Skills]]
