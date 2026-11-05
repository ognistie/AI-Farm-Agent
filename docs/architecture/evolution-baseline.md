# Evolução Live + Maestro: linha de base e plano

Base: commit `1bf0e4e`, branch `evolucao/live-maestro`. Toda mudança precisa de hipótese, benefício esperado e forma de
validar. Sem benefício medido, a implementação anterior fica.

## Linha de base (2026-11-05)

| Medida | Valor | Origem |
| --- | --- | --- |
| Testes sem custo | 201 de regressão, 546 de smoke | `unittest`, `smoke_code_agent.py` |
| Agente começa a falar, uso real | mediana 1,81 s, P90 3,47 s (n=10) | `latency_report.py --voice` |
| Tarefa começa, uso real | mediana 3,19 s (n=5) | idem |
| Tarefa termina, uso real | mediana 7,95 s (n=5) | idem |
| Sucesso declarado desde 01/11 | 15 de 21 | `history.jsonl` |
| Sucesso verificado desde 01/11 | 0 de 21 | `history.jsonl` |
| Custo por execução | mediana US$ 0,008, média US$ 0,016 | `history.jsonl` |
| Chamadas de modelo por execução | mediana 1 | `history.jsonl` |
| Interrompeu a pausa, API real | 3 de 4 | `eval_live_turns.py` |
| Delegação correta, API real | 6 de 6 | idem |
| Parar ao ser interrompido, API real | mediana 1,64 s | idem |

Sem medição ainda: ações duplicadas, recuperação após interrupção e violações de segurança, porque nada registrava isso.

## Metas fixadas antes de mudar

- Não interromper em pelo menos 9 de 10 pausas de 3 s.
- Nenhum pedido perdido.
- Tarefa começando em até 2 s, agente respondendo em até 1,2 s.

## Entregas

| # | Entrega | Situação |
| --- | --- | --- |
| 0 | Ponto de restauração e cenários | feita |
| 1 | Conversa natural | feita; metas ainda não comprovadas com voz humana |
| 2 | Registro de tarefas | feita |
| 3 | Autorização por efeito, começando só registrando | feita, em modo `shadow` |
| 4 | Verificação de cada passo | depende da 2 |
| 5 | Ponte Live e Maestro, com ID de tarefa, pausa e correção | depende da 2 e da 3 |
| 6 | Recuperação com conferência antes de repetir | depende da 2 e da 4 |
| 7 | Aprendizado por trajetórias | depende da 2 e da 4 |

## Correções do teste de 2026-11-05 (conversa + site)

| Problema real | Causa | Correção |
| --- | --- | --- |
| "Verificar o site" criou um projeto novo; "abrir no navegador" editou arquivos | O agente de código só tem criar e alterar | Só age com pedido de criar ou mudar; ver e abrir vão para `core/existing_targets.py` |
| Site "profissional" levou 4 min 24 s e falhou (US$ 0,36) | Resposta truncada em 16 mil tokens duas vezes | Raciocínio médio em site estático; após corte, pede versão menor |
| Navegador abriu `c/Users/...` como site | Caminho local tratado como endereço | Vira `file:///` se a página existe |
| "Pasta docs dentro de trabalhos" virou um caminho com a frase inteira | Extração de caminho sem subpasta | Resolve pasta dentro de pasta, por nome e por horário |
| "LLM não retornou nenhum step" em 5 pedidos de pasta | Pedido fora das ferramentas do agente de arquivos | Abrir o que existe sem modelo; mensagem explica o que dá para fazer |

## Autorização por efeito

`core/action_risk.py` classifica pelo que a ação toca: rótulo do botão, campo em que Enter envia texto, ou exclusão de
arquivo. Vale para o executor e dentro dos pilotos, antes de clicar. Começa em `shadow`: nada muda e
`memory/authorization.jsonl` guarda o que seria bloqueado, para medir falsos bloqueios antes do `enforce`.
`python -m core.action_risk` resume o registro. Limites: ícone sem rótulo não é reconhecido, e a confirmação vem do
texto do pedido ("confirmo"), ainda sem botão na interface.

## Fora do escopo, até a medição justificar

Motor externo de execução durável, banco vetorial, mais agentes, verificação por modelo como padrão, sandbox em máquina
virtual (o app não executa código gerado) e WebRTC.
