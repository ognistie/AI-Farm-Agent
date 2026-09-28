---
tipo: agente
agente: DATA
tags: [agente, data]
cssclasses: [agent-data]
missao: "Criar planilhas Excel profissionais com openpyxl: dados, fórmulas, formatação e gráficos."
cor: "#A78BFA"
playbooks: 3
skills: 3
---
# Data Agent

> [!data] Missão
> Criar planilhas Excel profissionais com openpyxl: dados, fórmulas, formatação e gráficos.

← [[Maestro]] · Políticas: [[Politicas de aceite]]

## Quando o Maestro chama
- criar planilha com dados
- relatório com gráfico
- fluxo de caixa, orçamento, cadastro, estoque

## Regras de execução
- Um passo `run_python` com o código completo; salva `.xlsx` na Área de Trabalho e abre no Excel.
- Nome do arquivo derivado da tarefa; nunca sobrescrever (sufixo _2).
- Colunas sugeridas são ponto de partida: adapte ao pedido.
- Fórmulas reais (=SUM, =AVERAGE) em vez de valores calculados no Python quando o usuário vai editar.
- Dados de exemplo variados e realistas; nunca dados pessoais reais.

## Como navegar e executar
- openpyxl: Workbook → cabeçalho formatado → dados → fórmulas → gráfico (BarChart/LineChart) → auto-largura → save → `start` no arquivo.

## Playbooks
- [[Playbook - Planilha com grafico]]
- [[Playbook - Fluxo de caixa]]
- [[Playbook - Lista e cadastro]]

## Skills
- [[senior-software-engineer]] — Código de produção com design coerente com o repositório, testes e erros explícitos.
- [[ai-product-strategist]] — Problema, resultado, métricas e riscos antes de construir com IA.
- [[ux-product-designer]] — Fluxos, arquitetura de informação e validação de usabilidade para reduzir atrito.

## Falhas conhecidas (e correção)
- Planilhas saíam sempre com o mesmo visual (cor #1F4E79 fixa). Agora a cor segue o tema.

## Subagentes
Três ajudantes executam junto com o agente — entender, montar, conferir:
- **1 · Entender** — [[SchemaDesigner]]: Descobre o tipo de planilha e sugere colunas iniciais.
- **2 · Montar** — [[FormulaChartDesigner]]: Decide formulas (SUM, AVERAGE...) e grafico conforme o pedido e o tipo.
- **3 · Conferir** — [[SheetReviewer]]: Revisa o codigo da planilha: sintaxe, salva .xlsx, nao sobrescreve, abre no Excel.

## Tarefas de referência
50 caminhos prontos para consulta:

![[Referencias.base#Data]]
