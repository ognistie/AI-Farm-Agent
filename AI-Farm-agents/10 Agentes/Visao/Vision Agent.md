---
tipo: agente-suporte
tags: [agente, suporte]
cssclasses: [agent-vision]
missao: "Localiza elementos na tela (OCR local primeiro, Claude Vision depois) para cliques e digitação quando não há API/UIA. Confiança baixa ou coo…"
cor: "#F87171"
---
# Vision Agent

> [!vision] Papel
> Localiza elementos na tela (OCR local primeiro, Claude Vision depois) para cliques e digitação quando não há API/UIA. Confiança baixa ou coordenada na barra de tarefas = falha.

← [[Maestro]]

## Cascata de localização
| Nível | Como | Custo | Quando |
|---|---|---|---|
| 1 | Ir direto: URL ou `open_path` | 0 | Endereço ou pasta conhecidos |
| 2 | UIA (acessibilidade do Windows) | 0 | Links do navegador (`browser_click`), botões de apps (`uia_click`) |
| 3 | Visão, 2 passos: tela reduzida → recorte em resolução cheia | ~US$ 0,007 | Ícones sem texto, apps sem UIA |

- Confiança mínima da visão: **50%** (antes 15%).
- Clique no navegador por visão é conferido: se título/URL não mudam, o passo falha.

## Skills
Referência de engenharia (este agente não recebe prompt com skills):
- [[performance-and-reliability-engineer]] — quando o pedido fala de lento, rapido, demora, pesado, travando, muitos arquivos… _(só documentação: este agente não planeja com o modelo)_

