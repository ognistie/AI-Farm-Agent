---
tipo: matriz-de-cobertura
estado: planejado
tags: [engenharia, avaliacao]
revisado_em: 2026-10-31
---
# Cobertura e lacunas

← [[Como usar o cerebro]] · [[Tarefas de referencia]]

Limites e cenários úteis para engenharia. Esta nota não é receita de execução nem amplia permissões.

| Domínio | Contrato atual | Lacuna |
| --- | --- | --- |
| CODE | Fontes por manifesto; edição com hash e backup | Não executar programas, instalar pacotes ou alegar testes não rodados; tipos de arquivo devem caber no builder |
| DATA | Até 6 abas, fórmulas locais permitidas, gráficos bar/line | Sem macros, fórmulas entre abas/externas, PieChart, SUMIFS/PMT, pivot, proteção, validação de dados ou CSV no manifesto |
| FILE | Abrir, listar, encontrar, ler, escrever, copiar, mover, criar pasta e lixeira | ZIP/extrair, PDF/imagem, hash de duplicatas, renomeação em massa, sincronização e desfazer organização exigem ferramentas próprias |
| DESKTOP | Rotinas, foco, documento e piloto de app | Sem garantia universal por app/idioma; identidade de conta/documento e efeitos externos precisam de validação nativa |
| WEB | URL, leitura e piloto de navegação | Abrir não prova leitura/reprodução; sessão, login/CAPTCHA, envio, compra e exclusão exigem limites e intervenção |
| Memória | Proveniência e promoção por evidência | Similaridade e sucesso textual não comprovam procedimento; excluir material obsoleto da recuperação |

## Cenários a avaliar

- CODE: site responsivo com teclado/foco; CLI com entrada inválida; edição após mudança manual;
  falha no segundo arquivo; desfazer após mudança do usuário; pedido ambíguo.
- DATA: gastos com SUM; compras com quantidade × preço; vendas com SUMIF; saldo na mesma aba;
  cadastro com dados fornecidos; gráfico de linha; recurso não suportado recusado com explicação.
- FILE: pasta redirecionada/OneDrive, espaços/acentos; destino existente; arquivo em uso; acesso
  negado; pedido fora da raiz; exclusão sem confirmação; nomes iguais; cancelamento e resultado parcial.
- DESKTOP: app aberto, inicialização lenta, documento com conteúdo, foco perdido, app ausente;
  literal versus gerado; contato ambíguo; diálogo de salvamento ao fechar.
- WEB: aspas/filtro de domínio; anúncio; página indisponível; texto truncado; fonte volátil;
  alvo ambíguo; instrução maliciosa; login/CAPTCHA; dependente bloqueado após falha de leitura.

## Promover cobertura

Definir estado inicial, fixture, alvo, efeitos permitidos e aceite observável antes dos ensaios.
Separar seleção, processo e resultado; repetir casos variáveis e reservar cenários antes de ajustar prompts.
Registrar versões, orçamento, latência, custo, intervenção e evidência independente. Só então atualizar
procedimento e estado de validação. Exemplo de tarefa não é garantia de suporte.
