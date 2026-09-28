---
tipo: tarefa-referencia
agente: WEB
contexto: "Navegação geográfica"
keywords: rota mapa mostre caminho ate avenida paulista
tags: [referencia, web]
cssclasses: [ref-note]
---
# Rota no mapa

> [!route] Pedido exemplo
> mostre no mapa o caminho até a avenida paulista

**Agente:** [[Web Agent]] · **Contexto:** Navegação geográfica

## Caminho
1. web_goto google.com/maps/dir/?api=1&destination=avenida+paulista
2. wait 3

## Forma alternativa
Maps search se não houver origem

## Critério de aceite
Rota exibida no Maps

## Armadilha
Localização do usuário depende do navegador

## Subagentes
- [[QueryBuilder]] — 1 · Entender
- [[Navigator]] — 2 · Montar
- [[ContentGuard]] — 3 · Conferir
