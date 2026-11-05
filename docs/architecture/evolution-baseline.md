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
| 3 | Autorização por efeito, começando só registrando | próxima |
| 4 | Verificação de cada passo | depende da 2 |
| 5 | Ponte Live e Maestro, com ID de tarefa, pausa e correção | depende da 2 e da 3 |
| 6 | Recuperação com conferência antes de repetir | depende da 2 e da 4 |
| 7 | Aprendizado por trajetórias | depende da 2 e da 4 |

## Fora do escopo, até a medição justificar

Motor externo de execução durável, banco vetorial, mais agentes, verificação por modelo como padrão, sandbox em máquina
virtual (o app não executa código gerado) e WebRTC.
