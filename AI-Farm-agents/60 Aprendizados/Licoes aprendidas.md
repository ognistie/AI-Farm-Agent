---
tipo: aprendizado
tags: [aprendizado]
cssclasses: [agent-memory]
atualizado: 2026-09-23
---
# 💡 Lições aprendidas

Cada falha real vira uma regra. ← [[Início]] · [[Tarefas com falha]]

> [!lesson] Pesquisar ≠ abrir o site
> "Abra o Google e pesquise X" só abria o Google: a rotina de abrir era checada antes da busca.
> **Regra:** pesquisa sempre vira URL de resultados · [[Web Agent]] · [[POL-003]]

> [!lesson] Conteúdo pedido precisa existir
> "Escreva a letra da música" gerou só o título. O prompt proibia inventar texto e nada conferia o resultado.
> **Regra:** criar conteúdo quando pedido; obra protegida → recusar com alternativa · [[POL-002]]

> [!lesson] Sucesso não é tentativa
> O circuit-breaker contava sucessos: repetir uma pesquisa fazia a 2ª ir para o LLM e a 4ª ser bloqueada.
> **Regra:** só falhas consecutivas contam · [[Web Agent]]

> [!lesson] Cancelar precisa parar de verdade
> Uma execução cancelada continuava viva e desligava a próxima tarefa.
> **Regra:** cada execução tem um token; a antiga não emite mais nada · [[Maestro]]

> [!lesson] Memória guarda caminho, não conteúdo
> A memória antiga reaproveitava planos inteiros e as respostas saíam sempre iguais.
> **Regra:** lembrar só a rota de agentes · [[Memory Agent]]

> [!lesson] Link se lê, não se adivinha
> Sem Playwright o agente só via pixels e errava links pequenos, ou "clicava" sem nada mudar.
> **Regra:** primeiro a árvore de acessibilidade do navegador (texto + URL reais), visão só no fim e sempre conferida · [[Web Agent]] · [[Vision Agent]]

> [!lesson] CAPTCHA é do usuário
> O Google mostrou "tráfego incomum" durante os testes.
> **Regra:** detectar a página de verificação e parar com aviso; nunca tentar resolver · [[Web Agent]]

> [!lesson] Regra por site não escala
> Rotas com regex erravam fora do padrão ("no mercado livre pesquise..." virava busca no Google; "segundo vídeo" era ignorado).
> **Regra:** rota fixa só para abrir/pesquisar; o resto vai para o piloto, que lê a página e decide. Listas mudam de ordem ao recarregar: depois de abrir o item certo, não volte para conferir · [[Web Agent]]

> [!lesson] Abrir app não é abrir documento novo
> O Bloco de Notas do Windows 11 reaproveita a janela (com abas): "abra o bloco de notas e escreva" colou texto num documento que o usuário já estava editando.
> **Regra:** antes de digitar, garantir documento **novo e sem alterações** (`blank_document`); na continuação, conferir que a aba ativa é a da conversa · [[Desktop Agent]] · [[Conversa continua]]

> [!lesson] Dica de vocabulário vira alucinação
> Uma lista de apps no prompt da transcrição fez o Whisper "ouvir" nomes que ninguém disse ("… O YouTube.").
> **Regra:** transcrição com dica neutra; nomes e gírias corrigidos **depois**, pelo [[Dicionario de voz]] + entendimento com contexto · [[Modo voz]]

> [!lesson] Na dúvida, perguntar UMA vez — nunca executar o palpite
> O agente adivinhava ("o meu, meu, meu Google") e repetia "não entendi" em loop.
> **Regra:** uma pergunta com o palpite; "sim" executa; se continuar sem entender, fica quieto · [[Modo voz]]

> [!lesson] Rótulo não é texto para digitar
> A POL-001 reprovou "abrir Bluetooth nas configurações" porque o Maestro pôs "Bluetooth" em `text`.
> **Regra:** só exigir digitação quando o pedido é escrever/enviar · [[POL-001]]

> [!lesson] Com algo aberto, quem decide se continua é a conversa — não uma lista de palavras
> "Clica em sistema" com as Configurações abertas virava pedido novo (não tinha "agora/esse") e reabria outra página.
> **Regra:** havendo alvo aberto e nenhum outro app citado, o resolvedor consulta a conversa · [[Conversa continua]]

> [!lesson] App já aberto não se reabre
> O Excel voltava para a tela inicial a cada pedido; "abre o Excel" virava resposta "já está aberto".
> **Regra:** continuar na janela da conversa (só trazer para a frente se o pedido for abrir); comando nunca vira resposta · [[Desktop Agent]]

> [!lesson] Abrir não é fazer
> Rotinas só abriam o app; "abre o Excel e preenche…" era reprovado ou feito com cliques chutados.
> **Regra:** rotina abre, o piloto de apps faz o resto na mesma janela; pedido de clicar sem passo que clique é reprovado (POL-007) · [[POL-007]]

> [!lesson] Regex de página precisa de palavra inteira
> "tema" dentro de "sis**tema**" abria Cores. **Regra:** `\b` sempre; e conferir o resultado em vez de declarar "concluída".

> [!lesson] Correção automática só para o que nunca é dito de propósito
> O dicionário trocava "ponto" por pontuação, "print" por "print (captura de tela)" e "vê esse código aqui" por VS Code.
> **Regra:** confusão `auto` só para fala que nunca é normal ("google escute"); o resto é `dica` para o modelo decidir pela frase · [[Confusoes de transcricao]]

> [!lesson] Não prometer o que não vai acontecer
> "Que horas são?" virava "já te falo as horas" e nada acontecia; "abre o..." virava "abrir algum aplicativo".
> **Regra:** responder na hora o que não precisa do PC; pedido cortado → perguntar o que falta · [[Modo voz]]

> [!lesson] Comentário não é pedido
> "Meu time ganhou ontem" virou uma pesquisa de placar que ninguém pediu.
> **Regra:** comentário vira conversa e pode OFERECER a ação; só executa com pedido ou aceite · [[Persona do assistente]]

> [!lesson] O que os agentes leem precisa estar certo
> Com o Obsidian virando fonte de todos os agentes, a nota do Desktop ainda mandava abrir o Excel e clicar no documento em branco pela visão.
> **Regra:** mudou o código, atualiza a nota do agente/playbook; execução registrada vale menos que playbook curado · [[Como usar o cerebro]]

> [!lesson] "Voltar para" tem dois sentidos
> "Voltar para o Excel" é trazer a janela; "voltar para a tela anterior" é navegar dentro do app. O atalho tratava os dois como trazer a janela — apareceu quando o Maestro mudou a redação.
> **Regra:** trazer pra frente só quando o resto da frase não fala de página/tela/aba/item; a avaliação de conversas pega mudanças de redação · [[Desktop Agent]] · [[Avaliacao de conversas]]

## Como revisar uma falha
1. Abra a nota em [[Tarefas com falha]].
2. Descubra a causa (plano? passo? ambiente?).
3. Registre aqui como lição e, se for padrão, crie um playbook ou uma política.
