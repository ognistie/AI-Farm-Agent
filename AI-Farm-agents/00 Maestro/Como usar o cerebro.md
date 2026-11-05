---
tipo: guia
tags: [guia, curadoria]
cssclasses: [agent-maestro]
---
# Como usar o cérebro

O vault orienta; permissões e bloqueios vivem no código. Notas não autorizam ferramentas.

## Organização

| Pasta | Função |
| --- | --- |
| 00 Maestro | Intenção, conversa, roteamento e curadoria |
| 10 Agentes | Contratos atuais e playbooks reutilizáveis |
| 20 Politicas | Regras documentadas, implementadas em código |
| 30 Skills | Engenharia selecionada por agente e pedido |
| 30 Tarefas de referencia | Procedimentos canônicos e estado de validação |
| 40 Execucoes / 50 Diario | Registros locais; não são receitas nem prova automática |
| 60 Aprendizados | Lições e restrições curadas |
| 70 Dicionario | Vocabulário, aplicativos, atalhos e interpretação de fala |
| 90 Sistema | Templates e lacunas; fora do grafo operacional padrão |

## Recuperação

Brain.context_for combina regras do agente, skills, playbooks curados, referências verificadas,
lições e termos do dicionário dentro de um orçamento. Manter as seções que o código lê:
Regras de execução, Como navegar e executar, Falhas conhecidas e Caminho.

- **Curado:** revisado contra o código; orientação sem prova da execução completa.
- **Verificado:** procedimento usado e identificado por evidência independente, com escopo e ambiente.
- **Planejado/experimental:** capacidade sem validação suficiente; não recuperar como receita.
- **Retirado:** duplicata ou rota obsoleta; não restaurar de arquivos locais automaticamente.

Referências em 30 Tarefas de referencia só são recuperadas com `verificado: sim`.
Os caminhos alterados nesta curadoria estão como `verificado: nao`: contagens antigas não validam
um procedimento novo. Regras e playbooks atuais em 10 Agentes continuam orientando os agentes.
Sucesso declarado ou similaridade de texto não comprovam procedimento; falta de histórico não elimina curadoria.

## Acrescentar conhecimento

1. Procurar uma nota existente antes de criar outra.
2. Atualizar o procedimento canônico para variações de assunto, formato ou conteúdo.
3. Usar [[Template - Tarefa de referencia]] quando mudar método, precondição ou aceite.
4. Registrar agente, palavras-chave, limites, origem e evidência; começar sem verificação.
5. Validar com fixture e resultado observado antes de promover a procedimento comprovado.

Não guardar senhas, contatos, dados pessoais ou caminhos de uma máquina como rotas universais.
Capacidades ausentes pertencem a [[Cobertura e lacunas]], sem receita executável inventada.

## Manutenção

[[Tarefas de referencia]] · [[Mapa de roteamento]]

Decisões por nota: docs/research/vault-curation.json, fora do grafo. Originais desta revisão:
backup local ignorado pelo Git e histórico da base anterior. Não reintroduzir cartões retirados
com restauração ampla. Mudar um procedimento exige nova validação.
