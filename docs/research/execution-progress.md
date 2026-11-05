# Execução do prompt de evolução — registro de progresso

> Registro da etapa anterior. O estado atualizado, as correções adicionais e as evidências
> da validação de liberação estão em [production-readiness.md](production-readiness.md).

Base: `d6d95cf`, mais as alterações locais preexistentes. Nenhum commit ou push nesta entrega.
As exclusões anteriores do vault foram preservadas para revisão; nenhuma restauração ampla foi feita.

## Estado por requisito

| Entrega do prompt | Estado | Implementado | Pendente para concluir |
| --- | --- | --- | --- |
| 1. Executor | Implementado parcialmente e verificado nos limites abaixo | Simulação central; worker fora da UI; exit status; timeout; cancelamento; Job Object; limites de saída, memória e processos; sem pip automático ou API keys no ambiente do worker | Sandbox de arquivos/rede e autorização universal; migração completa dos handlers legados; verificação em instalação limpa |
| 2. Orquestração | Implementado parcialmente | Dependências anteriores válidas; dependentes bloqueados após falha; interrupção de passos após erro; aprovação com token; slot ocupado até finalização; `verified` separado de `success` | Schemas completos, prazo/custo globais e condições de aceite de negócio por tarefa |
| 3. Agentes | Implementado parcialmente | FILE declarativo e escopo do pedido validado; colisão não sobrescreve; exclusão usa lixeira; resolução de pastas redirecionadas | Code/Data com verificadores de artefato e execução segura; mapear ferramentas dos demais agentes; operações FILE adicionais |
| 4. Navegação | Implementado parcialmente | Piloto Web observa a janela escolhida; pilotos rechecados para cancelamento após chamada ao modelo | Integração e versionamento de mapas, identidade estável de aba/documento e avaliação real por aplicativo |
| 5. Segundo cérebro | Implementado parcialmente | Similaridade/sucesso isolados não promovem notas; promoção exige referência e verificador; rotas sem evidência não são aprendidas | Produção de evidência confiável por domínio, esquema de validade/versão e avaliação de recuperação |
| 6. Voz | Implementado parcialmente | Erro/JSON/tipo inválido não vira comando; filas limitadas; áudio/entendimento anteriores ao cancelamento descartados | Corpus de áudio, eco, sotaques, latência e qualidade acústica; validação completa da UX |
| 7. Operação | Implementado parcialmente | Logs de ações omitem valores pessoais; caminho de log estável; capturas diagnósticas automáticas desativadas; dependências declaradas; CI ampliada | Retenção em todos os persistidores, migrações, lock de dependências, instalador e recuperação completa |

Nenhuma entrega ampla foi declarada concluída apenas por passar testes. A próxima dependência
crítica é uma fronteira de arquivos/rede para CODE/DATA e verificadores de resultado por domínio.

## Fronteiras e compatibilidade

- `AutomationEngine.execute` mantém `success/result/action`, acrescentando `status/verified`.
  Simulação retorna `status=simulated` e nunca chama handlers; `verified=False`.
- `_run_python` agora retorna resultado estruturado. Não altera CWD/stdout do assistente.
  O diretório relativo de artefatos fica em `memory/executions/<id>`; caminhos absolutos no código
  ainda têm permissões do usuário. `workspace` transfere somente valores JSON com limite.
- O worker usa Job Objects no Windows; falha de configuração impede liberar o código ao worker.
  Há até 8 processos e 1 GiB por job, limite de 120 s por chamada (Python usa 60; shell 30),
  monitoramento de saída de 1 MiB. O limite de disco é monitorado, não uma quota atômica.
- Descendentes do worker são encerrados também no fim normal. Abertura persistente de apps
  pertence às ferramentas Desktop; scripts que dependem de filhos persistentes precisam migrar.
- Instalações durante tarefas são recusadas. Dependências devem estar no ambiente preparado.
- FILE não aceita Python, shell ou acesso fora das raízes identificadas no pedido original.
  Ferramentas atuais: abrir, listar, encontrar, ler, criar pasta, copiar, mover e enviar à lixeira.
  Arquivamento, transformação e operações em massa sem inventário exigem implementação própria.
- A lixeira depende de `send2trash` e do suporte do volume. Falha não recai em exclusão permanente.
- Aprovação da UI passa `token` até o controller. Cancelar invalida a aprovação pendente.
- Flags antigas de verificação curada não são apagadas. Promoção nova requer
  `reference_evidence` produzido por código confiável; planos do modelo não preenchem esse campo.

Referência operacional: [Windows Job Objects](https://learn.microsoft.com/windows/win32/procthread/job-objects).
Jobs controlam processos e recursos; não constituem autorização de acesso a arquivos ou rede.

## Validação e limites

- Baseline dos novos testes do executor: reproduziu chamadas em simulação, liberação prematura
  do slot e conversão de falha de voz em comando; o novo runner ainda não existia.
- Regressões: `python -m unittest discover -s ai-farm-agent/tests -v`.
  Resultado observado: 32 testes aprovados. Compilação Python e `git diff --check` aprovados.
- Processos reais locais: sucesso/erro, CWD do pai preservado, código de saída, timeout,
  cancelamento, descendente que tenta criar marcador após encerramento, saída excessiva e
  remoção de segredo sintético do ambiente.
- Integração existente: seis grupos (`test_file_agent_skills`, `test_plan_policies`,
  `test_controller_run_token`, rodadas 7, 8 e 9) passaram, totalizando 77 verificações.
  Evidência de referência nos fixtures foi tornada explícita.
- QML: raiz carregada em plataforma offscreen com Bridge de teste e slot de aprovação validado.
  O teste precisou usar o diretório DLL do PySide6, como a entrada real já faz. Isso não é QA visual.
- Grader offline `core/outcome_grader.py`: seleção, processo e resultado separados; não aceita
  texto “done” como prova. Validado com arquivo ausente, errado, correto e recusas alternativas.
  Não mede estado de GUI nem qualidade de áudio.
- Não houve chamadas a modelos ou gravação de microfone. Não foi medido desempenho ponta a ponta.
  Python local 3.14, PySide6 6.11.2 e Windows. CI usa Python 3.12; a execução remota não foi observada.

## Próxima avaliação de capacidade

Separar casos de desenvolvimento e reservados antes de ajustar prompts. Incluir tarefas em
Calculadora, Explorador, navegador e planilhas com alvos, arquivos e estados iniciais definidos.
Executar ao menos três tentativas por caso variável; fixar modelo, ferramentas, orçamento e
critérios antes das tentativas. Medir seleção, resultado observado, ações indevidas, cancelamento,
intervenção, custo e latência separadamente. Não usar apenas sucessos do histórico como gabarito.

Matriz de suporte atual: contratos e processos validados localmente; cobertura de aplicativos,
isolamento de segurança, áudio e instalação limpa ainda não comprovados. Esses pontos impedem
declarar o produto pronto para produção.

## Migração e reversão

Não alterar em massa dados de sessão/vault. Implantar em ambiente de teste com arquivos de fixture.
Falha de simulação, perda de dados, alvo errado ou efeitos após cancelamento bloqueiam liberação.
Para reverter, isolar o diff desta entrega, considerando que ele compartilha arquivos com mudanças
anteriores; não usar reset amplo. Preservar artefatos e notas. Atribuição humana de responsáveis
pelas próximas entregas ainda não foi definida; não há prazo estimado sem avaliação do ambiente.
