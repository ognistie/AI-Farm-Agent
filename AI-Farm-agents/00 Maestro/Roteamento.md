---
tipo: processo
tags: [maestro, roteamento]
cssclasses: [agent-maestro]
---
# Roteamento

| Pedido | Agente | Exemplo |
|---|---|---|
| Criar código/projeto/arquivo de programação | [[Code Agent]] | "crie um site sobre café" |
| Editar arquivo de código existente | [[Code Agent]] | "adicione rota /login no app.py" |
| Planilha Excel com dados | [[Data Agent]] | "planilha de gastos com gráfico" |
| Pesquisar, abrir site, ler página | [[Web Agent]] | "pesquise eleições 2026" |
| Abrir app vazio ou interagir com app | [[Desktop Agent]] | "abra o bloco de notas e escreva..." |
| Organizar/mover/copiar arquivos | [[File Agent]] | "organize meus downloads" |

**Cadeias comuns:** pesquisar → enviar ([[Web Agent]] → [[Desktop Agent]] com `{output_summary_1}`).

**Proibido:** acoplar [[Code Agent]] + Desktop escrevendo o código no Bloco de Notas.
