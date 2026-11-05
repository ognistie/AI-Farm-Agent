# Curadoria do segundo cérebro — 2026-10-31

O proprietário autorizou manter conhecimento útil, retirar notas sem função e organizar a base
sem poluição. A curadoria avaliou o conteúdo das 237 referências excluídas na base `d6d95cf`,
as notas ainda presentes, os contratos atuais e as regras de recuperação.

## Resultado

- Recuperadas três referências úteis: edição de projeto, busca de arquivos e pesquisa no Google.
- Incorporado o conhecimento aproveitável das outras 234 referências em procedimentos,
  playbooks, regras de agente e matriz de lacunas.
- Consolidadas mais 15 notas presentes que repetiam esses procedimentos ou descreviam receitas antigas.
- Mantidos 15 procedimentos canônicos e 15 playbooks operacionais curados. Quatro playbooks de
  capacidades ausentes/experimentais permanecem como planejamento, fora da recuperação operacional.
- Preservados dicionário, skills, políticas, lições, registros locais, canvases e bases do Obsidian.

O [manifesto por nota](vault-curation.json) registra as 249 retiradas, o SHA-256 da versão
original no Git, o motivo e o substituto. Nenhuma retirada foi aprovada apenas por quantidade.
Conteúdo local anterior à edição foi copiado para
`ai-farm-agent/memory/vault-curation-2026-10-31/before/`; a leitura original das 237 notas está
no mesmo diretório em `deleted-baseline.json`. Esses backups são ignorados e não entram no prompt.
Não houve commit, push, alteração do index, reset ou reescrita de histórico.

## Critérios usados

Manter um procedimento quando método, precondição ou aceite acrescentam conhecimento.
Variações como poema/lista, tema de site, assunto de busca e cadastro de planilha usam a mesma
nota canônica. Casos negativos úteis foram preservados como limites e cenários de avaliação.

Foram retiradas receitas com Python/shell gerado, seletores/coordenadas fixos e promessas sem
ferramenta atual. Exemplos: compactação no FILE, fórmulas entre abas, 12 abas, PieChart,
envio automático de mensagens, fechamento repetido de janelas e inferência de duplicatas pelo nome.
Isso não remove uma capacidade implementada; deixa de anunciar como suportada uma receita incompatível.

As regras de CODE, DATA e FILE foram alinhadas com manifestos/ferramentas atuais. Informações
de caminhos privados foram evitadas. Contagens de sucesso antigas não foram transferidas aos
procedimentos novos: referências modificadas estão `verificado: nao`, aguardando evidência de uso
e resultado. Regras e playbooks curados em `10 Agentes` continuam fornecendo contexto aos agentes.

## Organização e manutenção

Início, mapa de roteamento, índice, guia e template foram alinhados com a estrutura real.
O grafo padrão exclui templates e registros de execução/diário; não foi preciso apagar logs pessoais
ou desenhos para reduzir ruído. Removidos favorito vazio e atalho de rascunho sem título; arquivo
de rascunho preservado. Links de conhecimento são auditados, incluindo distinção entre Markdown
e views `.base` de mesmo nome.

O runtime filtra notas planejadas, experimentais e retiradas antes da recuperação. Ferramentas
de restauração/verificação consultam o manifesto e recusam reintroduzir notas retiradas do arquivo
antigo. Manifesto inválido ou substituto ausente falha explicitamente, sem restaurar a fonte.

A recuperação lexical considera também cobertura dos termos do pedido: um playbook consolidado
não perde relevância apenas por possuir mais palavras-chave que um cartão curto. Essa alternativa
exige ao menos dois termos coincidentes e cobertura de metade do pedido; escopo por agente e
filtros de estado continuam valendo. Testes distinguem consulta pertinente de correspondência
genérica isolada e agente errado. Reaparecimento de nota retirada suspende a recuperação de
procedimentos até corrigir a inconsistência, impedindo exposição do conteúdo obsoleto ao modelo.
Não foi medido ganho universal de recuperação nem executado benchmark com embeddings.

A suíte antiga presumiu inicialmente que toda referência deveria ser verificada e que envio no
WhatsApp deveria recuperar uma receita. Essas expectativas foram substituídas por validação do
estado explícito e abstenção para envio experimental. A regressão real de recuperação de busca
e cadastro após a consolidação foi corrigida e testada; nenhuma evidência foi inventada para
transformar procedimentos revisados em execuções comprovadas.

```powershell
.\.venv\Scripts\python.exe ai-farm-agent/scripts/check_vault.py
.\.venv\Scripts\python.exe ai-farm-agent/scripts/check_release.py
```

Testes cobrem restauração, promoção indevida, manifesto inválido, substituto ausente, hash
divergente, exclusão nova sem revisão, filtro de contexto e links. A curadoria resolve a pendência
das notas; os bloqueios de produção descritos em [production-readiness.md](production-readiness.md)
continuam válidos. A CI remota e o commit candidato ainda precisam ser revisados antes de publicar.

Validação final executada: 60 testes de regressão e 537 verificações numéricas da suíte de smoke
aprovados; compilação, dependências, QML, integridade de links e whitespace aprovados.
O gate confirmou 249 exclusões com curadoria correspondente, zero exclusões pendentes e fontes
inalteradas durante a rodada: `code_ready=true`, `main_ready=true`, `production_ready=false`.
`main_ready` é o resultado do gate local, não autorização de push ou certificação de produção.
