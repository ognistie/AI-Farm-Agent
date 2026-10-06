---
tipo: benchmark
tags: [benchmark, custo]
cssclasses: [agent-maestro]
---
# 💰 Benchmark de custo — AI Farm x Claude Cowork x ChatGPT Work

← [[Maestro]] · [[Avaliacao de voz]] · [[Avaliacao de conversas]]

> [!info] Rodada 2026-10-06T12:02:22 → 2026-10-06T12:18:53 · 30 tarefas × 2 repetições · sucesso 59/60
> **AI Farm = medido** (cada chamada ao modelo, tokens e custo reais). **Cowork e ChatGPT Work = estimados**: custo de API de um agente de tela com o MESMO número de passos que nós precisamos (premissa favorável a eles), nos cenários *enxuto* (favorável a eles) e *típico*. Gerado por `scripts/bench_cost.py`.

## Resultado (soma das tarefas, média por repetição)

| Sistema | Custo das tarefas | Quantas vezes o AI Farm é mais barato |
|---|---|---|
| **AI Farm (medido)** | **US$ 0.5760 (R$ 3.082)** | — |
| Claude Cowork — enxuto (Sonnet 5.5) | US$ 0.5388 (R$ 2.883) | **0.9×** |
| Claude Cowork — típico (Opus 5.5) | US$ 1.4456 (R$ 7.734) | **2.5×** |
| ChatGPT Work — enxuto (GPT-6 Sol) | US$ 0.4822 (R$ 2.580) | **0.8×** |
| ChatGPT Work — típico (GPT-6 Sol) | US$ 0.7410 (R$ 3.964) | **1.3×** |

## Por categoria

| Categoria | Tarefas | AI Farm | Cowork (enxuto–típico) | ChatGPT Work (enxuto–típico) |
|---|---|---|---|---|
| DESKTOP | 11 | US$ 0.1427 | US$ 0.1952–0.5679 (1.4×–4.0×) | US$ 0.1646–0.2856 (1.2×–2.0×) |
| WEB | 10 | US$ 0.1606 | US$ 0.1659–0.4814 (1.0×–3.0×) | US$ 0.1399–0.2417 (0.9×–1.5×) |
| CODE | 3 | US$ 0.1727 | US$ 0.1312–0.2651 (0.8×–1.5×) | US$ 0.1312–0.1399 (0.8×–0.8×) |
| FILE | 1 | US$ 0.0606 | US$ 0.0077–0.0313 (0.1×–0.5×) | US$ 0.0077–0.0181 (0.1×–0.3×) |
| DATA | 1 | US$ 0.0347 | US$ 0.0287–0.0583 (0.8×–1.7×) | US$ 0.0287–0.0316 (0.8×–0.9×) |
| CHAT | 4 | US$ 0.0047 | US$ 0.0102–0.0416 (2.2×–8.8×) | US$ 0.0102–0.0240 (2.2×–5.1×) |

## Por tarefa

| | Tarefa | Sucesso | Passos | Chamadas | AI Farm (mín–máx) | Cowork típ. | ChatGPT típ. |
|---|---|---|---|---|---|---|---|
| d01 | abre o bloco de notas e escreve: lista de compras: arroz, fe | 2/2 | 3 | 3 | US$ 0.0090 (0.0089–0.0091) | US$ 0.0682 | US$ 0.0344 |
| d02 | agora escreve embaixo: comprar pão também | 1/2 | 0 | 4 | US$ 0.0131 (0.0103–0.0159) | US$ 0.0334 | US$ 0.0167 |
| d03 | abre a calculadora e calcula 128 vezes 47 | 2/2 | 3 | 5 | US$ 0.0148 (0.0137–0.0159) | US$ 0.0682 | US$ 0.0344 |
| d04 | abre as configurações do windows | 2/2 | 1 | 2 | US$ 0.0057 (0.0057–0.0057) | US$ 0.0334 | US$ 0.0167 |
| d05 | abre a página de bluetooth nas configurações | 2/2 | 1 | 3 | US$ 0.0093 (0.0092–0.0094) | US$ 0.0334 | US$ 0.0167 |
| d06 | abre as configurações do windows | 2/2 | 1 | 2 | US$ 0.0057 (0.0057–0.0057) | US$ 0.0334 | US$ 0.0167 |
| d07 | clica em sistema | 2/2 | 2 | 5 | US$ 0.0176 (0.0170–0.0183) | US$ 0.0506 | US$ 0.0254 |
| d08 | abre o excel e preenche a primeira linha com Produto, Preço  | 2/2 | 6 | 10 | US$ 0.0444 (0.0378–0.0510) | US$ 0.1121 | US$ 0.0569 |
| d09 | abre o paint | 2/2 | 1 | 2 | US$ 0.0047 (0.0046–0.0047) | US$ 0.0334 | US$ 0.0167 |
| d10 | abre o bloco de notas e escreve um poema curto sobre café | 2/2 | 3 | 3 | US$ 0.0095 (0.0095–0.0095) | US$ 0.0682 | US$ 0.0344 |
| d11 | abre a tela de bloqueio nas configurações | 2/2 | 1 | 3 | US$ 0.0089 (0.0084–0.0094) | US$ 0.0334 | US$ 0.0167 |
| w01 | pesquisa no google previsão do tempo em São Paulo | 2/2 | 2 | 2 | US$ 0.0066 (0.0065–0.0067) | US$ 0.0506 | US$ 0.0254 |
| w02 | abre o youtube e pesquisa lofi para estudar | 2/2 | 1 | 3 | US$ 0.0085 (0.0084–0.0086) | US$ 0.0334 | US$ 0.0167 |
| w03 | abre o segundo vídeo | 2/2 | 3 | 6 | US$ 0.0310 (0.0238–0.0381) | US$ 0.0682 | US$ 0.0344 |
| w04 | entra na wikipédia e me diz em que ano foi fundada a cidade  | 2/2 | 2 | 6 | US$ 0.0396 (0.0318–0.0473) | US$ 0.0594 | US$ 0.0299 |
| w05 | pesquisa o preço do fone JBL Tune 520 no mercado livre e me  | 2/2 | 3 | 6 | US$ 0.0310 (0.0296–0.0323) | US$ 0.0682 | US$ 0.0344 |
| w06 | abre o g1 | 2/2 | 2 | 4 | US$ 0.0136 (0.0135–0.0137) | US$ 0.0506 | US$ 0.0254 |
| w07 | pesquisa no youtube receita de pão de queijo | 2/2 | 1 | 2 | US$ 0.0058 (0.0058–0.0059) | US$ 0.0334 | US$ 0.0167 |
| w08 | abre o github | 2/2 | 1 | 2 | US$ 0.0046 (0.0046–0.0047) | US$ 0.0334 | US$ 0.0167 |
| w09 | quanto tá o dólar hoje? | 2/2 | 2 | 3 | US$ 0.0080 (0.0079–0.0081) | US$ 0.0506 | US$ 0.0254 |
| w10 | abre o site da receita federal | 2/2 | 1 | 4 | US$ 0.0120 (0.0119–0.0121) | US$ 0.0334 | US$ 0.0167 |
| c01 | cria um site simples para a padaria Pão Dourado com html e c | 2/2 | 1 | 4 | US$ 0.0806 (0.0717–0.0895) | US$ 0.1351 | US$ 0.0700 |
| c02 | muda a cor do título para roxo | 2/2 | 1 | 4 | US$ 0.0496 (0.0444–0.0548) | US$ 0.0666 | US$ 0.0358 |
| c03 | cria um script python que conta quantas palavras tem num tex | 2/2 | 1 | 4 | US$ 0.0425 (0.0422–0.0429) | US$ 0.0634 | US$ 0.0342 |
| f01 | organiza a pasta C:\Users\Guilherme\Documents\bench_ai_farm_ | 2/2 | 1 | 5 | US$ 0.0606 (0.0597–0.0615) | US$ 0.0313 | US$ 0.0181 |
| t01 | faz uma planilha de gastos mensais com 5 categorias e o tota | 2/2 | 1 | 4 | US$ 0.0347 (0.0344–0.0351) | US$ 0.0583 | US$ 0.0316 |
| q01 | que horas são | 2/2 | 0 | 0 | US$ 0.0000 (0.0000–0.0000) | US$ 0.0104 | US$ 0.0060 |
| q02 | quanto é 15% de 320 | 2/2 | 0 | 1 | US$ 0.0016 (0.0016–0.0016) | US$ 0.0104 | US$ 0.0060 |
| q03 | quem escreveu Dom Casmurro | 2/2 | 0 | 1 | US$ 0.0015 (0.0014–0.0015) | US$ 0.0104 | US$ 0.0060 |
| q04 | valeu, ficou ótimo | 2/2 | 0 | 1 | US$ 0.0017 (0.0016–0.0017) | US$ 0.0104 | US$ 0.0060 |

## De onde vem a economia (medido nas 60 execuções)

- **Leitura da tela por texto (acessibilidade) em vez de captura:** 38 leituras, ~1107 tokens cada, contra ~1533 de uma captura 1920×1200 (e a captura entra de novo no histórico a cada passo). Capturas enviadas ao modelo: 6.
- **Rotinas sem modelo:** 53 passos executados sem chamar a IA (um agente de tela pagaria cada um; a ~US$ 0.0067 por passo do nosso piloto = ~US$ 0.353 poupados).
- **Respostas na hora sem modelo (voz):** 16/60 falas entendidas por atalho/resposta local.
- **Cache de prompt:** 319,169 tokens lidos do cache (de 569,162 de entrada) = US$ 0.575 poupados.
- **Modelo e esforço:** Sonnet 5 com esforço baixo/médio. Os mesmos tokens no Opus 5.5 custariam US$ 2.240 em vez de US$ 1.152 (1.9×).
- **Contexto enxuto:** cada chamada leva só o necessário (sem reenviar a conversa inteira nem capturas antigas).

### Quanto o AI Farm custaria sem cada método (por repetição das 30 tarefas)

| Configuração | Custo | vs. atual |
|---|---|---|
| Atual (medido) | US$ 0.576 | 1,0× |
| Sem cache de prompt | US$ 0.863 | 1.5× |
| Sem rotinas (todo passo pela IA) | US$ 0.753 | 1.3× |
| Com Opus 5.5 em vez de Sonnet 5 | US$ 1.120 | 1.9× |
| Sem cache, sem rotinas e com Opus | US$ 2.022 | 3.5× |

### Para onde vai o custo do AI Farm

| Etapa | Chamadas | Custo | Parte |
|---|---|---|---|
| CODE | 6 | US$ 0.293 | 25% |
| MAESTRO | 53 | US$ 0.212 | 18% |
| WEB_PILOT | 23 | US$ 0.173 | 15% |
| REPLY | 52 | US$ 0.112 | 10% |
| VOICE | 44 | US$ 0.106 | 9% |
| FILE | 4 | US$ 0.103 | 9% |
| APP_PILOT | 15 | US$ 0.080 | 7% |
| DATA | 2 | US$ 0.052 | 5% |
| VISION | 6 | US$ 0.021 | 2% |

> [!tip] Próxima economia
> Maestro + entendimento de voz + resposta final são uma camada fixa em todo pedido. Rotear direto os pedidos simples (abrir, pesquisar) e responder com frase pronta quando não há dado a contar cortaria boa parte dela.

## Quanto o usuário paga por mês

Os dois concorrentes cobram **assinatura** com limite de uso (janelas de 5 h); nenhum publica custo por tarefa. Com o custo médio medido por tarefa do AI Farm:

| Pedidos/mês | AI Farm (R$) | ChatGPT Plus | Claude Pro (Cowork) |
|---|---|---|---|
| 150 | R$ 15.41 | R$ 99,90 (6.5×) | R$ 106.99 (6.9×) |
| 300 | R$ 30.82 | R$ 99,90 (3.2×) | R$ 106.99 (3.5×) |
| 600 | R$ 61.63 | R$ 99,90 (1.6×) | R$ 106.99 (1.7×) |
| 900 | R$ 92.45 | R$ 99,90 (1.1×) | R$ 106.99 (1.2×) |
| 1500 | R$ 154.08 | R$ 99,90 (0.6×) | R$ 106.99 (0.7×) |

Custo médio por tarefa medido: **R$ 0.103** · empate com o Plus: **973 pedidos/mês** · com o Claude Pro: **1042 pedidos/mês**.

## Premissas

- Câmbio: US$ 1 = R$ 4.97 + 4% spread do cartão + 3.5% IOF.
- Preços de API (US$/1M entrada · saída · cache): claude-sonnet-5 (nosso): 2.0 · 10.0 · 0.2; claude-opus-5-5 (Cowork tipico): 4.0 · 20.0 · 0.2; claude-sonnet-5-5 (Cowork enxuto): 2.0 · 10.0 · 0.2; gpt-6-sol (ChatGPT Work): 2.0 · 10.0 · 0.2.
- Captura de tela 1920×1200: Claude ~1533 tokens, OpenAI ~1105 tokens (fórmula pública de visão; GPT-6 pode diferir).
- Cenários do agente de tela: **enxuto**: sistema 4000 tokens (cacheado), 1 captura(s) no histórico, 150 tokens de saída por passo; **tipico**: sistema 8000 tokens (cacheado), 3 captura(s) no histórico, 400 tokens de saída por passo.
- Passos dos concorrentes = passos que NÓS precisamos + 1 para conferir (um agente de tela costuma precisar de mais). Código/planilha/arquivos: ferramentas de arquivo, sem captura, e no mínimo o mesmo texto gerado.
- Não medido: qualidade comparada e limites reais das assinaturas (dependem de rodar as mesmas tarefas nas contas do usuário).

## Fontes
- Preços ChatGPT (BR): https://chatgpt.com/pt-BR/pricing/
- GPT-6 Sol API: https://www.eesel.ai/blog/gpt-6-sol-pricing
- Claude Cowork nos planos: https://fast.io/resources/claude-cowork-pricing-plans/
- Limites ChatGPT Work: https://www.ai-toolbox.co/chatgpt-management-and-productivity/chatgpt-limits-messages-tokens-rate-2026
- Preços da API Claude: tabela oficial de modelos da Anthropic (Sonnet 5 $2/$10; Opus 5.5 $4/$20; Sonnet 5.5 $2/$10).
