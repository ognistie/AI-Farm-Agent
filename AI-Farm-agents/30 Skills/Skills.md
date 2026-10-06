---
tipo: indice
tags: [skill, indice]
cssclasses: [skill-note]
---
# Skills do catálogo

Skills do [AIWorkbench](https://github.com/BielmFranco/AIWorkbench) transformadas em **manual de uso** para os agentes. ← [[Início]] · [[Como usar o cerebro]]

> [!info] Como funcionam
> A cada pedido, o agente recebe as **1 a 3 skills mais relevantes** dele (`core/skills.py`): as marcadas como *sempre* para aquele agente e as cujas palavras de **ativa_quando** aparecem no pedido. Vai para o prompt: o que faz, **como o agente aplica** (só as linhas daquele agente), as regras e o que **conferir antes de concluir**. O plano no Obsidian registra quais skills foram usadas.
>
> [!tip] Ajustar
> Edite a nota da skill: `ativa_quando` (palavras do pedido), `sempre_para`, e as linhas `- **Agente:** …` em *Como o agente aplica*. O app relê sozinho. Skill é **referência**: nunca amplia permissões (as travas vivem em código).

| Skill | Agentes | Sempre para | Ativa quando o pedido fala de |
|---|---|---|---|
| [[senior-software-engineer]] | Code Agent, Data Agent, File Agent | Code Agent, Data Agent, File Agent | script, programa, codigo, automacao, funcao, python, calcular, gerar, converter, processar… |
| [[full-stack-architect]] | Code Agent | — | api, backend, servidor, banco de dados, sqlite, login, cadastro, sistema, crud, flask, fas… |
| [[frontend-experience-engineer]] | Code Agent | — | site, pagina, html, css, javascript, landing, formulario, botao, menu, responsivo, celular… |
| [[premium-ui-designer]] | Code Agent | — | site, landing, pagina, visual, bonito, moderno, elegante, premium, profissional, design, l… |
| [[design-system-architect]] | Code Agent | — | identidade visual, paleta, cores, tema, tema escuro, modo escuro, padronizar, componentes,… |
| [[code-review-and-refactoring-expert]] | Code Agent | — | muda, troca, altera, corrige, conserta, ajusta, melhora, refatora, bug, erro, quebrou, nao… |
| [[ux-product-designer]] | Desktop Agent, Data Agent, Code Agent | Desktop Agent | planilha, tabela, cadastro, formulario, controle, organizar, lista, agenda, relatorio, fac… |
| [[ai-agent-engineer]] | Desktop Agent, Web Agent, Maestro | Desktop Agent, Web Agent, Maestro | clica, abre, entra, navega, preenche, toca, executa, automatiza, faz pra mim… |
| [[performance-and-reliability-engineer]] | Desktop Agent, File Agent, Code Agent, Vision Agent | — | lento, rapido, demora, pesado, travando, muitos arquivos, grande, milhares, otimiza, perfo… |
| [[security-and-guardrails-engineer]] | File Agent, Web Agent, Maestro, Desktop Agent, Code Agent | File Agent, Web Agent | apaga, deleta, exclui, remove, limpa, envia, manda, compartilha, senha, login, conta, paga… |
| [[rag-knowledge-engineer]] | Web Agent, Memory Agent, Maestro | — | pesquisa, procura, busca, le, ler, resume, resumo, qual, quanto, preco, cotacao, noticia, … |
| [[context-and-prompt-engineer]] | Maestro, Web Agent | — | resume, explica, escreve, texto, redige, email, mensagem, post, prompt, instrucao, conteud… |
| [[ai-evaluation-engineer]] | Code Agent, Memory Agent, Maestro | — | teste, testes, testar, validar, avaliar, conferir, verifica, garante, qualidade, benchmark… |
| [[tech-lead]] | Maestro | — | e depois, em seguida, depois, projeto, sistema completo, varias, varios, etapas, passo a p… |
| [[ai-product-strategist]] | Data Agent, Maestro, Code Agent | — | ideia, negocio, startup, produto, estrategia, plano de negocio, mvp, metricas, kpi, mercad… |

![[Skills.base]]
