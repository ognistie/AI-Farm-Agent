---
tipo: avaliacao
tags: [avaliacao, conversa]
cssclasses: [agent-maestro]
---
# 🧪 Avaliação de conversas

← [[Conversa continua]] · [[Modo voz]] · [[Roteiro de testes]]

> [!info] Última rodada: 2026-10-05 — 28/28 cenários ok, US$ 0.165
> Gerado por `scripts/eval_conversations.py --vault` (sem executar nada no PC).

| | Cenário | Fala | Entendeu | Alvo | Agentes | Ações | Problema |
|---|---|---|---|---|---|---|---|
| ✅ | config: clica em sistema | clica em sistema | continue | app:configuracoes | DESKTOP | app_task | - |
| ✅ | config: entra em acessibilidade | agora entra em acessibilidade | continue | app:configuracoes | DESKTOP | app_task | - |
| ✅ | config: ativa o modo escuro | ativa o modo escuro | continue | app:configuracoes | DESKTOP | app_task | - |
| ✅ | config: volta | volta pra página anterior | continue | app:configuracoes | DESKTOP | app_task | - |
| ✅ | excel: abre o excel (ja aberto) | abre o excel | continue | app:excel | DESKTOP | focus_window | - |
| ✅ | excel: preenche coluna | preenche a coluna A com os meses do ano | continue | app:excel | DESKTOP | app_task | - |
| ✅ | excel: alfabeto nas colunas | preencher as colunas A, B e C com as letras do alfabeto | continue | app:excel | DESKTOP | app_task | - |
| ✅ | excel: abrir e escrever do zero | abre o excel e escreve nome, idade e cidade na primeira linha | new | - | DESKTOP | app_search, wait, vision_click, wait, app_task | - |
| ✅ | notepad: abrir e escrever | abre o bloco de notas e escreve de 1 até 10 | new | - | DESKTOP | app_search, wait, blank_document, app_type | - |
| ✅ | notepad: continuar escrevendo | agora escreve um poema curto sobre o mar | continue | app:notepad | DESKTOP | focus_window, app_type | - |
| ✅ | notepad: outro bloco de notas | abre outro bloco de notas | new | - | DESKTOP | app_search, wait, blank_document | - |
| ✅ | calc: continuar a conta | agora divide por 4 | continue | app:calculadora | DESKTOP | app_task | - |
| ✅ | calc: abrir e calcular | abre a calculadora e calcula 15 por cento de 200 | new | - | DESKTOP | app_search, wait, app_task | - |
| ✅ | youtube: segundo vídeo | abre o segundo vídeo | continue | web | WEB | browser_task | - |
| ✅ | youtube: pula o vídeo | pula esse vídeo | continue | web | WEB | browser_task | - |
| ✅ | youtube: config do windows (app novo) | abre as configurações do windows | new | - | DESKTOP | open_path | - |
| ✅ | youtube: pergunta sobre a lista | qual era o nome do primeiro vídeo? | question | - | - | - | - |
| ✅ | youtube: outra pesquisa | pesquisa no google a previsão do tempo pra hoje | new | - | WEB | run_python, wait, wait, browser_read | - |
| ✅ | loja: preço do segundo | e o segundo, quanto custa? | question | - | - | - | - |
| ✅ | code: muda a cor do título | muda a cor do título pra vermelho | continue | code | CODE | edit_project | - |
| ✅ | code: desfaz | desfaz | undo | code | - | - | - |
| ✅ | code: troque algumas coisas | troque algumas coisas | clarify | code | - | - | - |
| ✅ | pasta: organiza essa pasta | organiza essa pasta por tipo de arquivo | continue | folder | FILE | run_python | - |
| ✅ | geral: abrir vs code | abrir vs code | new | - | DESKTOP | app_search, wait | - |
| ✅ | notepad: fecha esse | fecha esse bloco de notas | continue | app:notepad | DESKTOP | app_task | - |
| ✅ | youtube: e o terceiro? | e o terceiro? | continue | web | WEB | browser_task | - |
| ✅ | papo: valeu (texto) | valeu, era isso | question | - | - | - | - |
| ✅ | excel: salva a planilha | salva essa planilha como vendas | continue | app:excel | DESKTOP | app_task | - |
