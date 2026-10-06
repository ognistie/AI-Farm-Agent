---
tipo: skill
origem: AIWorkbench
agentes: [CODE]
sempre_para: []
ativa_quando: api, backend, servidor, banco de dados, sqlite, login, cadastro, sistema, crud, flask, fastapi, rotas, endpoint, app web, aplicativo
tags: [skill]
cssclasses: [skill-note]
atualizado: 2026-10-05
---
# full-stack-architect

> [!skill] O que faz
> Arquitetura coerente com responsabilidades claras, caminhos de falha e trade-offs explícitos.

**Usada por:** [[Code Agent]]

## Quando usar
- API, sistema com banco de dados, login/cadastro, app com backend

Ativa sozinha quando o pedido fala de: api, backend, servidor, banco de dados, sqlite, login, cadastro, sistema, crud, flask, fastapi, rotas, endpoint, app web, aplicativo.

## Como o agente aplica
- **Code Agent:** Monolito simples primeiro: um app (Flask/FastAPI) + SQLite, separado em rotas, modelos e serviços.
- **Code Agent:** Valide toda entrada da API; responda erros com status certo (400/404/500) e mensagem útil.
- **Code Agent:** Senhas sempre com hash (nunca em texto puro); segredos em variável de ambiente, nunca no código.
- **Code Agent:** Inclua um README curto: como instalar, rodar e testar.

## Regras
- Não usar microsserviços por padrão
- Não desenhar componente sem responsabilidade
- Não omitir caminhos de falha

## Conferir antes de concluir
- Cada arquivo tem uma responsabilidade clara
- Entradas inválidas não derrubam o app
- Nenhum segredo fixo no código

## Fluxo (catálogo)
1. Traduzir requisitos em atributos de qualidade
2. Modelar domínios, fronteiras de confiança e dados
3. Escolher a topologia mais simples
4. Definir APIs, consistência e retries
5. Planejar segurança, logs e recuperação

Fonte: [AIWorkbench](https://github.com/BielmFranco/AIWorkbench/tree/main/skills/full-stack-architect) · como os agentes usam: [[Skills]]
