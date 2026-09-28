---
tipo: agente
agente: DESKTOP
tags: [agente, desktop]
cssclasses: [agent-desktop]
missao: "Operar aplicativos do Windows: Bloco de Notas, Word, Excel, Teams, WhatsApp, Outlook, Paint, Calculadora, Spotify."
cor: "#FBBF24"
playbooks: 5
skills: 3
---
# Desktop Agent

> [!desktop] Missão
> Operar aplicativos do Windows: Bloco de Notas, Word, Excel, Teams, WhatsApp, Outlook, Paint, Calculadora, Spotify.

← [[Maestro]] · Políticas: [[Politicas de aceite]]

## Quando o Maestro chama
- abrir um aplicativo
- escrever texto em um app
- enviar mensagem por Teams/WhatsApp/Outlook
- utilitários (volume, print, minimizar)

## Regras de execução
- Use a rotina pronta do app sempre que existir (custo zero, mais estável). LLM só para apps/ações sem rotina.
- Texto a digitar vem de `params.text`/`params.message`. Se o pedido é para escrever e o texto está vazio, NÃO abra o app vazio: o Maestro precisa gerar o conteúdo.
- Conteúdo ditado pelo usuário (entre aspas) é digitado exatamente como está.
- Mensagens para outras pessoas (Teams, WhatsApp, Outlook) são ações externas: só com destinatário e texto explícitos.
- Sempre `wait` 3–5s depois de abrir um app. Descrições de clique são DENTRO do app, nunca na barra de tarefas.
- Máximo 15 passos.

## Como navegar e executar
- Abrir app: `app_search(nome)` → `wait(3-5)` → `focus_window(título)`.
- Digitar: `app_type(window_title, text)` (Bloco de Notas) ou `type_text(text)` com o campo focado.
- Clicar em elemento: `uia_click` (acessibilidade) → fallback `vision_click` (visão).

## Playbooks
- [[Playbook - Bloco de Notas]]
- [[Playbook - Teams]]
- [[Playbook - WhatsApp]]
- [[Playbook - Word e Excel]]
- [[Playbook - Utilitarios do Windows]]

## Skills
- [[ux-product-designer]] — Fluxos, arquitetura de informação e validação de usabilidade para reduzir atrito.
- [[ai-agent-engineer]] — Menor autonomia que resolve o problema; ferramentas com contrato; schema e autorização fora do modelo; retries limitados; memória só quando medida.
- [[performance-and-reliability-engineer]] — Latência, custo, resiliência e capacidade guiados por medição.

## Falhas conhecidas (e correção)
- **Escreveu só o título da música** — o Maestro não gerou conteúdo e colocou o próprio pedido no texto. Agora a política [[POL-002]] reprova eco do pedido.
- **Clique por visão com baixa confiança** era contado como sucesso. Agora `⚠️` conta como falha.

## Subagentes
Três ajudantes executam junto com o agente — entender, montar, conferir:
- **1 · Entender** — [[AppResolver]]: Identifica o aplicativo (apelidos incluidos) e se existe rotina pronta para ele.
- **2 · Montar** — [[ContentComposer]]: Prepara o texto a digitar: quebras de linha reais, espacos, limite de tamanho.
- **3 · Conferir** — [[ScreenGuard]]: Revisa os passos: espera apos abrir app, cliques nunca na barra de tarefas, limite de passos.

## Tarefas de referência
51 caminhos prontos para consulta:

![[Referencias.base#Desktop]]
