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

## Como revisar uma falha
1. Abra a nota em [[Tarefas com falha]].
2. Descubra a causa (plano? passo? ambiente?).
3. Registre aqui como lição e, se for padrão, crie um playbook ou uma política.
