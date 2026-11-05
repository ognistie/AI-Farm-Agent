# Evolução do AI Farm Agent — primeira entrega

## Diagnóstico e limites

O fluxo atual liga voz/texto, sessão, Maestro, agentes, motor de automação e observação.
O vault fornece contexto; logs de execução são locais. Os pilotos já observam UI Automation
e dispõem de fallback visual. Os mapas em `state_maps/` ainda precisam de avaliação de
validade por versão, idioma e estado da interface. Não há evidência de cobertura universal.

A inspeção confirmou perda de fontes na verificação/arquivamento do vault, recuperação
sem filtro por agente, execução de palpites classificados como incertos e leitura de
planilhas que materializava todas as linhas. A primeira entrega trata esses limites
sem trocar modelos, infraestrutura ou arquitetura de agentes.

## Contratos entregues

- `verify_all`: somente notas com histórico correspondente recebem novos campos; fontes
  não são removidas. Histórico ausente/vazio não revoga curadoria existente.
- `restore_references`: cópia explícita das referências arquivadas, sem substituir notas
  existentes ou apagar o arquivo. `scripts/brain_verify.py --restore` é idempotente.
  Não foi executado no vault do usuário; as exclusões anteriores permanecem para revisão.
- `vault_audit.py --apply`: anota a reprovação e mantém a fonte no vault.
- `find_references`: filtro opcional por agente antes do ranking e exclusão de caminhos
  vazios. Maestro pode consultar todos os domínios. Proveniência continua em `note`.
- Voz `unclear`: pergunta antes de enfileirar; “sim” confirma e “não” cancela o palpite.
- XLSX: estatísticas em uma passagem, até 10 mil linhas, 128 colunas e seis abas.
  Prévia de 80 linhas e resposta de 12 mil caracteres; leitura limitada é marcada PARCIAL.
  Fórmulas não são avaliadas e soma de coluna não é apresentada como total contábil.

Dados externos continuam sendo referência; permissões pertencem ao motor/validador.
O sucesso registrado por semelhança lexical ainda NÃO equivale a validação independente
do procedimento. Separar essas duas evidências é requisito da próxima entrega.

## Evidência local

Comando: `python -m unittest discover -s ai-farm-agent/tests -v`.
Python local: 3.14; openpyxl: 3.1.5. A CI usa Python 3.12 e executa a mesma suíte.
Os oito primeiros casos tiveram 1 aprovação, 3 falhas e 4 erros antes do patch
(após corrigir o diretório temporário do ambiente). Após o patch passaram os oito.
Foram acrescentados casos de restauração, recusa de contexto, fechamento em falha
e confirmação/negação por voz. São regressões determinísticas, não benchmark de IA.
Resultado final: 12 testes novos aprovados e 48 verificações dos grupos existentes
`test_round7_fluid_conversation`, `test_round8_spreadsheet_reader` e
`test_round9_brain_speed_app` aprovadas. Compilação Python e checagem de whitespace aprovadas.
Não foram medidos STT, qualidade de áudio, latência de modelos ou sucesso em apps reais.

## Sequência de entregas

| Entrega | Responsável | Dependência | Critério de saída |
| --- | --- | --- | --- |
| 1. Preservação, recuperação e limites | IA desenvolvedora desta sessão | Estado atual | Regressões locais aprovadas, fontes preservadas |
| 2. Evidência de execução | IA desenvolvedora; revisão humana dos casos | 1 | Estado final observado separado de sucesso declarado; referência não promovida só por Jaccard |
| 3. Navegação por estado | IA desenvolvedora; usuário fornece ambiente de validação | 2 | App, versão/idioma, precondição, transição e pós-condição registrados; mapa inválido recupera ou interrompe |
| 4. Experiência de voz | IA desenvolvedora; validação humana de áudio | 1 e 2 | Cancelamento, sobreposição e continuação avaliados em áudio; latências p50/p95 registradas |

O caminho crítico para navegação confiável é 1 → 2 → 3. Não há prazo estimado sem
medir o ambiente, os aplicativos escolhidos e a disponibilidade de testes reais.

## Protocolo da próxima avaliação de IA

Fixar modelo, configuração, versão do harness, orçamento e critérios antes das execuções.
Separar conjunto de desenvolvimento de um conjunto reservado, sem ajustar limiares pelo
resultado reservado. Executar ao menos três tentativas por cenário variável:

1. Abrir Calculadora e calcular; repetir com outro app em foco.
2. Continuar na mesma aba; distinguir duas janelas do mesmo aplicativo.
3. Elemento desaparece, UI muda de idioma, mapa obsoleto e timeout.
4. Voz com nome ambíguo, autocorreção, ditado, interrupção e cancelamento da fila.
5. Nota parecida de agente errado, fonte desatualizada e instrução maliciosa em página.

Registrar separadamente seleção do agente/referência, resultado observado, ação indevida,
pedidos de esclarecimento, chamadas, custo e latência por etapa. Comparar baseline e
candidato no mesmo ambiente. Manter reservado o áudio de usuários com consentimento;
não versionar conversas pessoais ou credenciais.

Antes de liberar, testar o avaliador com resultados corretos, incorretos e alternativas
válidas. Bloquear liberação por ação indevida ou perda de dados. Em regressão, reverter
somente o patch correspondente, preservando notas e alterações preexistentes.
