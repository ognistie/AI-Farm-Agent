# Pesquisa: Claude Cowork, ChatGPT Work, voz em tempo real e memória de agentes

Pesquisa feita em 20/10/2026 (busca semântica Exa + leitura das páginas). O objetivo é entender como os dois
produtos de referência funcionam e aplicar as ideias ao AI Farm Agent sem copiar a interface de ninguém.

## O que eles fazem

### Claude Cowork (Anthropic)
- Mesma arquitetura de agente do Claude Code, dentro do Claude Desktop (Mac e Windows), sem terminal.
  Você descreve o resultado, sai e volta para o trabalho pronto. [overview][cw-overview]
- Lê e escreve arquivos locais; usa o computador (clicar, digitar, abrir apps) quando não há conector.
  [computer use][cw-computer]
- **Projetos**: pastas locais + instruções fixas + links + **memória própria do projeto**; cada sessão já
  começa com esse contexto. [projects][cw-projects]
- Divide trabalho complexo em subtarefas paralelas; entrega planilhas com fórmulas, apresentações, documentos.
- Revisa o plano antes de mexer em arquivos; ações importantes pedem aprovação.

### ChatGPT Work (OpenAI, lançado em 09/07/2026)
- Agente que trabalha por horas num projeto, dividindo em passos e concluindo sozinho; cria docs, planilhas,
  slides e web apps a partir de apps e arquivos. [anúncio][oa-work] · [Reuters][reuters]
- Você **acompanha o progresso, responde perguntas, muda a direção e aprova ações importantes** no meio.
- **Tarefas agendadas** continuam trabalhando sem você.
- No app desktop: Chat e Work na mesma janela, Codex à parte; voz e navegador por cima de tudo. [ajuda][oa-desktop]

### Voz em tempo real (OpenAI)
- Três arquiteturas: **GPT-Live** (full duplex: o modelo de voz conversa enquanto um backend separado faz o
  trabalho), Realtime API (um modelo só) e **pipeline encadeado** (STT → agente → TTS, inspecionável — é o
  nosso caso). [voice agents][oa-voice]
- O que medir: tempo até a resposta **audível**, **silêncio indesejado**, sobreposição e quanto o agente
  **cede quando interrompido**; reconhecimento de nomes e números.
- Detecção de fim de fala por silêncio (server VAD) ou por sentido (semantic VAD). [VAD][oa-vad]

### Memória de agentes
- Memória ≠ contexto. Tipos com políticas diferentes (CoALA): de trabalho, episódica (o que aconteceu),
  semântica (fatos) e **procedimental** (como fazer) — a mais perigosa de envenenar. [artigo][mem-article]
- **MemGuard**: as duas falhas são **admissão não confiável** (trajetórias que falharam ou deram certo por
  acaso entram porque parecem relevantes) e **deriva** (duplicadas, velhas, conflitantes). Antes de guardar,
  verificar se deu certo de verdade; guardar falha como **restrição**, nunca como receita. [paper][memguard]

### Acesso rápido (apps desktop)
- Claude: atalho de qualquer lugar abre a caixa de pedido; anexa print/janela; ditado. [quick entry][cl-quick]

## O que aplicamos (rodada 9)

| Ideia | No AI Farm Agent |
|---|---|
| Memória só verificada (MemGuard) | Referência só orienta com `verificado: sim` (deu certo de verdade); hipóteses fora do vault, voltam quando uma execução real dá certo; falha demais rebaixa (`core/memory_gate.py`) |
| Tipos de memória (CoALA) | procedimento (referências) · restrição (lições) · vocabulário (dicionário) · registro (execuções, nunca no prompt) |
| Roteamento visível | `00 Maestro/Mapa de roteamento` gerado das execuções reais |
| Projetos / instruções do Cowork | **Instruções personalizadas** (Configurações) em todo pedido |
| Revisar plano e aprovar (Cowork/Work) | Opção **Revisar o plano antes de executar** (Executar / Cancelar) |
| Acesso rápido | **Alt+Espaço** de qualquer app abre o mini chat com foco |
| Anexar arquivos | **+** e arrastar-e-soltar; "resume esta planilha" lê o arquivo |
| Silêncio indesejado (GPT-Live) | sinal sonoro "ouvi" na hora em que a fala termina; interrupção falando (rodada 6) |
| Latência | raciocínio desligado onde medido sem perda (Maestro 3,1 s → 1,7 s) e plano enxuto (213 → 130 tokens) |

## Próximos passos (não feitos; precisam de medição)
- **Full duplex de verdade** (GPT-Live): o modelo de conversa continua falando com você enquanto o backend
  trabalha — hoje a voz confirma, enfileira e avisa progresso, mas não "conversa" durante a tarefa.
- **Juntar entendimento da fala e plano numa chamada** (hoje, pedido novo por voz = 2 chamadas em série).
- **Projetos** com pastas e memória por projeto; **tarefas agendadas**.
- Transcrição mais rápida exige outro hardware (sem GPU NVIDIA aqui) ou um serviço externo.

[cw-overview]: https://claude.com/docs/cowork/overview
[cw-projects]: https://claude.com/docs/cowork/guide/projects
[cw-computer]: https://support.claude.com/en/articles/14128542-let-claude-use-your-computer-in-cowork
[cl-quick]: https://support.claude.com/en/articles/12626668-use-quick-entry-with-claude-desktop-on-mac
[oa-work]: https://openai.com/index/chatgpt-for-your-most-ambitious-work/
[reuters]: https://www.reuters.com/business/openai-launches-chatgpt-work-2026-07-09/
[oa-desktop]: https://help.openai.com/en/articles/20001276-moving-to-the-new-chatgpt-desktop-app
[oa-voice]: https://developers.openai.com/api/docs/guides/voice-agents
[oa-vad]: https://developers.openai.com/api/docs/guides/realtime-vad
[mem-article]: https://valdemird.com/learn/agentic-systems/memory/
[memguard]: https://arxiv.org/html/2608.21867
