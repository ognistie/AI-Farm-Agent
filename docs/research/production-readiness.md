# Avaliação de liberação — 2026-10-31

**Decisão: não publicar como produção. A pendência de curadoria foi resolvida.**
As verificações locais de código passaram. As exclusões de referências foram avaliadas e
consolidadas por autorização do proprietário; a automação autônoma de interfaces ainda não
tem evidência suficiente de segurança e confiabilidade. O repositório já está na branch `main`; isso não significa que as alterações
locais estejam publicadas. Nenhum commit, push, reset ou restauração ampla foi executado nesta etapa.

Base: `d6d95cf`, com alterações locais preexistentes. Este relatório não atribui todo o diff
a uma única entrega. Das 237 referências originalmente excluídas, três foram recuperadas e
234 consolidadas; outras 15 duplicatas/receitas antigas foram incorporadas às notas canônicas.
O conjunto final contém 15 procedimentos e 249 retiradas documentadas com hash, motivo e substituto
em [vault-curation.json](vault-curation.json). Originais preservados no histórico e em backup local.

## Implementação e contratos

- **CODE:** manifesto de até 40 arquivos/1 MiB, caminhos relativos validados, tipos de arquivo
  delimitados, validação de sintaxe Python/JSON e diretório de destino novo. O conteúdo gravado
  é conferido por SHA-256. A aplicação não executa o programa gerado. Sintaxe e integridade
  não comprovam correção funcional nem segurança do programa para execução manual.
- **DATA:** manifesto de até seis abas, 5.000 linhas por aba, 100 colunas e 1 MiB; células,
  fórmulas locais permitidas e gráficos declarativos. O XLSX é reaberto e suas abas, células,
  fórmulas e quantidade de gráficos são conferidas. Não se afirma que fórmulas tenham sido
  recalculadas pelo Excel ou que a renderização do gráfico tenha sido validada.
- **Planejamento:** saídas estruturadas JSON no provedor, validação determinística e uma
  tentativa adicional limitada após manifesto inválido. Erros por tentativa são registrados.
- **Execução:** `run_python`, `run_command` e `pip_install` são recusados pelo dispatcher;
  ferramentas são limitadas pelo agente definido pelo controller. FILE revalida raízes
  derivadas do pedido original. Dry-run retorna antes de invocar qualquer handler.
- **Edição e recuperação:** leitura com hash, detecção de arquivo alterado durante planejamento,
  staging, backup, publicação com rollback em falha detectada e verificação do conteúdo.
  Desfazer valida todos os arquivos e backups antes da primeira alteração, preserva alterações
  posteriores do usuário e tenta rollback em falha parcial. Versões antigas sem hashes exigem
  restauração manual. Não há promessa de transação durável entre vários arquivos após queda de energia.
- **Desktop e Web:** foco confirmado antes de operações selecionadas; terminal não aceita ditado
  genérico; fechar aplicativo usa a janela correspondente e preserva diálogos nativos, sem matar
  processos por nome. Navegação nativa usa URL HTTP/HTTPS, sem Python gerado. Identidade completa
  de documento/conta e autorização de efeitos consequentes ainda estão incompletas.
- **Worker interno:** controle de timeout, cancelamento, descendentes e recursos por Job Object;
  saída drenada com limite, sem arquivos temporários de stdout sujeitos a bloqueios. Continua
  com permissões do usuário e não constitui sandbox de filesystem/rede.
- **Persistência:** substituição atômica de configurações/workflows com tentativas limitadas
  para bloqueios transitórios do Windows; falha persistente propaga erro e preserva o arquivo anterior.
- **Operação:** configuração e `.env` resolvidos por caminhos explícitos; instalação durante
  tarefas desativada; ambiente Windows/Python 3.11 com versões fixadas, script de setup e CI.

## Evidências executadas

Os arquivos completos ficam em `ai-farm-agent/memory/`, ignorados pelo Git. A tabela é um
registro local, não substitui a execução da CI no commit final.

| Verificação | Resultado e limite |
| --- | --- |
| Ambiente limpo | Venv novo, Python 3.11.9; dependências de runtime e voz instaladas; `pip check` aprovado |
| Compilação | Módulos Python do aplicativo, scripts e testes aprovados |
| Regressões | 60 testes, incluindo executor, cancelamento, dry-run, autorização, manifests, edição/undo, curadoria, recuperação e bloqueio de restauração de notas retiradas |
| Smoke existente | 41 grupos executados; 537 verificações numéricas em 37 resumos, todos aprovados |
| Interface | QML carregado e renderizado em 1280×820 com Bridge de fixture; imagem inspecionada; não é teste da sessão nativa Windows |
| Dependências | 67 pacotes auditados; zero vulnerabilidades conhecidas no resultado final; sem garantia sobre vulnerabilidades desconhecidas |
| Segredos no diff candidato | 310 arquivos de texto candidatos inspecionados por padrões de chaves Anthropic/OpenAI/AWS e chaves privadas, sem correspondências não-placeholder; um caminho pessoal em benchmark foi anonimizado; não é varredura universal nem revisão do histórico |
| CODE/DATA com API real | Regressão 6/6 e conjunto reservado 6/6, três tentativas por agente em cada conjunto; arquivos efetivamente lidos pelos graders |
| Áudio local sintético | Piper produziu áudio; faster-whisper reconheceu “Abre a calculadora.”; sem microfone humano, eco ou interrupção |
| Integridade da validação | Digest de fontes antes/depois; alterações durante a execução invalidam o resultado; `git diff --check` aprovado |
| CI remota | Workflow preparado; execução no GitHub não observada |
| Curadoria | 15 procedimentos canônicos, 15 playbooks ativos, nenhum link quebrado na base de conhecimento auditada; 249 retiradas com substituto e origem documentados |

Antes de saídas estruturadas, uma avaliação inicial de manifests teve 4/6 sucessos. O registro
inicial não tinha detalhe suficiente para atribuir uma causa única às falhas. Depois da alteração,
a regressão e os cenários reservados passaram. O conjunto é pequeno e não permite extrapolar
uma taxa de sucesso universal. Cenários reservados não foram usados para ajustar prompts.

CODE teve latência de geração aproximada de 41–64 s; DATA, 2–4 s. O esforço registrado para
CODE foi `high`, inclusive em fixtures pequenas: latência segue sendo um problema de produto.
No áudio sintético, TTS levou 9,72 s incluindo carregamento; a etapa de decodificação STT levou
6,43 s. Isso não mede latência ponta a ponta nem comprova experiência de conversa responsiva.

Evidências: `release-check.json`, `release-check/*.txt`, `dependency-audit-fixed.json`,
`release-live-regression.json`, `release-live-holdout.json`, `synthetic-audio-evaluation.json`
e `ui-release.png`. Não publicar automaticamente registros que possam conter dados locais.

## Matriz de suporte demonstrado

| Superfície | Cobertura comprovada |
| --- | --- |
| Windows local + Python 3.11.9 | Instalação limpa, contratos, processos, artefatos e renderização Qt offscreen |
| CODE/DATA | Geração sem execução em fixtures sintéticas pequenas; leitura real dos arquivos e múltiplas tentativas |
| FILE | Contratos e limites exercitados por testes; operações arbitrárias em dados pessoais não foram realizadas |
| Desktop/Web | Testes de guardas e mocks; falta matriz nativa por aplicativo, versão, idioma e estado inicial |
| Voz | Uma frase sintética; falta corpus humano e cenários de interrupção, ruído e eco |
| Outros Python/Windows | Não certificados por esta rodada; o lock suportado é específico de Windows/Python 3.11 |

## Bloqueios para publicação

1. **Escopo de dados — resolvido:** proprietário autorizou retirar material sem utilidade e
   organizar o conhecimento aproveitável. Curadoria registrada por nota, com bloqueio de
   restauração automática de receitas retiradas. Procedimentos modificados aguardam revalidação;
   contagens antigas não são usadas para promovê-los.
2. **Autorização por efeito:** fechar a fronteira de envio, compra, exclusão e alterações
   persistentes em GUI. Limitar ferramentas por agente e verificar foco não substitui autorizar
   cada efeito. Browser/app pilots continuam experimentais.
3. **Desktop real:** ensaios com contas e arquivos de fixture, cobrindo alvo errado, perda de foco,
   pré-requisito ausente, timeout, cancelamento e ausência de efeitos após parar; definir uma
   lista pequena e explícita de tarefas suportadas antes de ampliar cobertura.
4. **Voz real:** gravações representativas, confiança baixa, ditado versus comando, correções,
   sotaques, eco e interrupção; medir acerto e latência ponta a ponta contra critérios prévios.
5. **Credenciais históricas:** confirmar revogação das chaves expostas anteriormente no histórico;
   nenhuma rotação foi realizada aqui. Limpar o diff atual não resolve exposição histórica.
6. **Operação e avaliação:** executar CI no commit candidato; testar atualização/recuperação,
   retenção de dados locais e recuperação do segundo cérebro. Completar benchmarks de recuperação
   e navegação por estado, orçamento global de tarefas e evidência de resultado por aplicativo.

O gate relata `code_ready`, `main_ready` e `production_ready` separadamente. `main_ready`
representa apenas verificações locais e ausência de exclusões sem decisão registrada; revisão do escopo,
CI e avaliação humana continuam necessárias. `production_ready` permanece falso enquanto
os critérios de produção acima não forem implementados e demonstrados.

Após a curadoria, a rodada local completa aprovou os 60 testes e a suíte de smoke, com
`code_ready=true`, `main_ready=true` e zero exclusões sem revisão. As 249 retiradas conferem
com o hash das fontes na base e possuem substitutos existentes. Esse resultado permite
revisar um candidato de integração; não transforma o produto em pronto para produção.

## Reproduzir

Na raiz, com Python 3.11 instalado:

```powershell
.\scripts\setup.ps1
.\.venv\Scripts\python.exe ai-farm-agent/scripts/check_release.py --code-only
.\.venv\Scripts\python.exe ai-farm-agent/main.py
```

O setup reutiliza `.venv` existente somente se a versão Python for 3.11. Não remove ambientes.
Configure a chave no `.env` local antes de iniciar. Sem `--code-only`, exclusões do vault sem
curadoria correspondente também fazem o gate sair com erro. O manifesto precisa identificar
a nota, o hash exato da fonte na base e um substituto existente; novas exclusões não são
aprovadas por uma contagem ou por uma flag global. O gate local não chama modelos nem opera o desktop pessoal.

Avaliação opcional com API, explicitamente cobrada pelo provedor:

```powershell
.\.venv\Scripts\python.exe ai-farm-agent/scripts/eval_release_artifacts.py --allow-live --split regression --trials 3
.\.venv\Scripts\python.exe ai-farm-agent/scripts/eval_release_artifacts.py --allow-live --split holdout --trials 3
```

Para reversão, revisar e isolar o diff desta entrega; ele compartilha arquivos com trabalho
anterior. Preservar backups e notas, sem `reset --hard`, limpeza ampla ou reescrita de histórico.
