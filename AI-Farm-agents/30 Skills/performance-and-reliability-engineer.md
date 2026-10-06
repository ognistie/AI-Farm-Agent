---
tipo: skill
origem: AIWorkbench
agentes: [DESKTOP, FILE, CODE, VISION]
sempre_para: []
ativa_quando: lento, rapido, demora, pesado, travando, muitos arquivos, grande, milhares, otimiza, performance, desempenho, esperar, carregar
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# performance-and-reliability-engineer

> [!skill] O que faz
> Melhorar velocidade e estabilidade de forma repetível, sem sacrificar a correção.

**Usada por:** [[Desktop Agent]] · [[File Agent]] · [[Code Agent]] · [[Vision Agent]]

## Quando usar
- Pastas grandes, apps lentos, pedidos de otimização

Ativa sozinha quando o pedido fala de: lento, rapido, demora, pesado, travando, muitos arquivos, grande, milhares, otimiza, performance, desempenho, esperar, carregar.

## Como o agente aplica
- **Desktop Agent:** Espere por condição (janela/título apareceu), não por tempo fixo longo; tempo fixo só como teto.
- **Desktop Agent:** Se o app não responder, não repita o clique: espere, confira e reporte.
- **File Agent:** Pasta grande: percorra com os.scandir/pathlib em streaming, sem carregar tudo na memória; mostre progresso por contagem.
- **File Agent:** Duplicados: compare tamanho primeiro e hash só nos candidatos.
- **Code Agent:** Evite laços aninhados sobre os mesmos dados (N²) e consultas dentro de laço (N+1).
- **Code Agent:** Meça antes de 'otimizar'; diga o ganho com número.

## Regras
- Não concluir a partir de micro-benchmark
- Evitar N+1 e concorrência sem limite
- Medir antes e depois

## Conferir antes de concluir
- Não ficou travado esperando à toa
- Funciona com volume grande
- Ganho afirmado foi medido

## Fluxo (catálogo)
1. Definir carga, linha de base e metas
2. Medir ponta a ponta
3. Uma hipótese, uma variável por vez
4. Comparar com carga representativa
5. Conferir correção, memória e saturação

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/performance-and-reliability-engineer) · como os agentes usam: [[Skills]]
