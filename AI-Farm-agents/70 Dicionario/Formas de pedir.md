---
tipo: dicionario
tags: [dicionario, voz]
cssclasses: [agent-maestro]
atualizado: 2026-10-05
---

# 🗣️ Formas de pedir — da fala à execução

← [[Dicionario de voz]]

> [!info] Uso
> Como os pedidos aparecem na fala do dia a dia → a **intenção** → **como o agente executa** e se precisa **confirmar**. Vai para o entendimento de voz (corrigir o pedido) e para os agentes (escolher o caminho).
>
> [!warning] Ações com consequência
> Enviar, publicar, apagar, comprar, pagar e desligar: o agente **prepara e confirma**. Pagamento/transferência nunca é feito pelo agente.

## Abrir, fechar e janelas

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| abre / abra / abri / abrir / abre aí / abre pra mim / abre lá / me abre / dá uma abrida / puxa / chama o | abrir app ou site | app: rotina do app (exe direto); site: URL do **Abrir com**; se já está aberto, só traz pra frente | não | abre aí o youtube pra mim |
| entra no / entra em / vai no / vai pro / vai pra / acessa / chega no / passa no / cai no | ir para (site ou app) | igual a abrir; dentro de um site aberto, navega nele | não | vai no google |
| abre outro / abre uma nova / abre mais um / nova janela / outra aba | abrir NOVA instância | nunca reaproveita a janela aberta | não | abre outro bloco de notas |
| volta pro / volta no / me leva de volta / retorna pro | trazer de volta algo já aberto | foca a janela/aba existente da conversa | não | volta pro excel |
| fecha / fecha aí / fecha isso / mata / mata o app / encerra / sai do / some com | fechar | fecha a janela EM FOCO da conversa (não todas do app); documento sem salvar → pergunta | se houver algo sem salvar | fecha esse bloco de notas |
| minimiza / esconde / tira da frente / joga pra baixo | minimizar | minimiza a janela em foco (Win+↓) | não | minimiza tudo |
| maximiza / tela cheia / deixa grande / amplia a janela | maximizar | Win+↑; vídeo: F ou F11 | não | deixa o vídeo em tela cheia |
| alterna / troca de janela / muda pro outro | alternar janela | Alt+Tab ou foca pelo título | não | muda pro chrome |

## Pesquisar, ler e perguntar

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| pesquisa / pesquise / procura / busca / dá um google / joga no google / dá uma olhada em / vê pra mim / googla | pesquisar | Web: URL de resultados (google.com/search?q=…); dentro de um site aberto, usa a busca dele | não | joga no google receita de bolo |
| pesquisa no youtube / procura no youtube / acha um vídeo de | pesquisar no YouTube | youtube.com/results?search_query=… | não | procura no youtube lofi |
| procura no mercado livre / acha na amazon / vê o preço de / quanto tá o | pesquisar produto/preço | busca no site citado e lê os primeiros resultados com preço | não | vê o preço do iphone no mercado livre |
| lê / lê pra mim / me fala o que tá escrito / o que diz aí / o que tem aí | ler a tela/página | lê a página aberta (texto real da acessibilidade) e resume | não | lê essa notícia pra mim |
| resume / faz um resumo / me dá a ideia geral / resumão / tl;dr | resumir | lê e resume em 3–5 frases | não | resume essa página |
| traduz / passa pra inglês / passa pro português / como se diz | traduzir | responde direto ou usa o Tradutor | não | traduz isso pra inglês |
| me mostra / mostra / me fala / me diz / qual é / quanto tá / quanto custa / quanto é | informar | dado do momento → pesquisa; conta/conhecimento → responde direto | não | quanto tá o dólar |
| calcula / faz a conta / quanto dá / soma / subtrai / multiplica / divide / porcentagem de | calcular | conta simples: responde direto; na Calculadora só se pedir | não | quanto dá doze vezes sete |

## Agir na tela e no texto

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| clica / clique / aperta / aperte / seleciona / escolhe / marca / dá um clique / toca em (botão) | clicar / selecionar | piloto lê a tela e clica pelo NOME do elemento; visão só como último recurso | não | clica no segundo |
| rola / desce / desce a página / rola pra baixo / mais pra baixo | rolar para baixo | scroll na janela em foco | não | desce mais um pouco |
| sobe / sobe a página / rola pra cima / volta pro topo | rolar para cima | scroll para cima / Home | não | sobe a página |
| atualiza / dá um f5 / recarrega / recarregar | recarregar a página | F5 na aba em foco | não | dá um f5 aí |
| volta / voltar / página anterior / retorna | voltar (navegador) | Alt+← na aba em foco; em projeto de código = desfazer | não | volta a página |
| avança / próxima página / vai pra frente | avançar (navegador) | Alt+→ | não | avança a página |
| escreve / escreva / digita / anota / bota escrito / redige / rascunha / põe aí | escrever / digitar | documento em branco garantido (nunca no arquivo do usuário) e digita o texto; ditado vai literal | não | anota aí: reunião às três |
| preenche / completa / coloca na célula / põe na coluna / lança na planilha | preencher (planilha/formulário) | piloto de apps: vai para a célula/campo e digita (Tab/Enter entre células) | não | preenche a primeira linha com nome e idade |
| apaga tudo / limpa o texto / seleciona tudo e apaga | limpar texto | Ctrl+A e Delete no documento EM FOCO | não | apaga tudo e escreve bom dia |
| copia / ctrl c / copiar / copia isso | copiar | Ctrl+C (seleção) ou copia o texto pedido | não | copia esse link |
| cola / ctrl v / colar / cola aqui | colar | Ctrl+V no campo em foco | não | cola aqui |
| desfaz / ctrl z / volta como tava / volta como era | desfazer | Ctrl+Z; em projeto de código restaura o backup | não | desfaz isso |
| salva / salvar / guarda / grava / salva como | salvar | Ctrl+S; nome novo → Salvar como (pergunta o nome se faltar) | não | salva esse arquivo |
| imprime / manda imprimir / imprimir | imprimir | Ctrl+P e confirma a impressora | sim | imprime essa página |
| printa / tira um print / tira uma foto da tela / captura a tela | capturar tela | print da tela (ou Win+Shift+S para recorte) | não | printa a tela |

## Música e vídeo

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| toca / tocar / dá um play / dá play / solta o som / manda o som / põe pra tocar / roda / bota pra tocar | tocar / reproduzir | abre o item e dá play (YouTube: clica no vídeo; Spotify: busca e toca) | não | dá um play nesse vídeo |
| pausa / pausar / para a música / segura aí / dá um pause / dá um tempo | pausar | tecla de mídia ou K/espaço no player em foco | não | pausa o vídeo |
| continua a música / despausa / volta a tocar | retomar | tecla play/pause | não | volta a tocar |
| pula / pular / passa / próxima / avança a música / passa essa | próxima faixa/item | tecla próxima faixa ou Shift+N no YouTube | não | pula essa música |
| anterior / volta a música / a de antes | faixa anterior | tecla faixa anterior | não | volta a música |
| aumenta / sobe / mais alto / no talo / no máximo / aumenta o som | aumentar volume | teclas de volume (passos) ou volume 100% | não | aumenta o som |
| abaixa / diminui / mais baixo / dá uma baixada / abaixa o som | diminuir volume | teclas de volume | não | abaixa o volume |
| muta / mudo / tira o som / silencia / desmuta / volta o som | silenciar / reativar som | tecla mudo | não | muta o pc |
| legenda / liga a legenda / tira a legenda | legendas | C no YouTube / menu de legendas | não | liga a legenda |
| acelera / mais rápido / velocidade 2x / deixa mais devagar | velocidade do vídeo | Shift+> / Shift+< no YouTube | não | acelera o vídeo |

## Mensagens, publicações e compras

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| manda / envia / dispara / joga pra / passa pra / encaminha / manda pro | enviar | prepara a mensagem e **confirma** destinatário e texto antes de enviar | **sim** | manda pro joão no zap |
| chama no zap / dá um zap / manda um zap / chama no whats / manda mensagem | mensagem no WhatsApp | abre a conversa, escreve e **confirma** antes de enviar | **sim** | dá um zap pra minha mãe |
| manda um email / escreve um email / responde o email | e-mail | rascunho no Gmail/Outlook; envio só com confirmação | **sim** | manda um email pro chefe |
| liga / liga pra / faz uma ligação / dá uma ligada / chama no teams | ligar (chamada) | abre a chamada e **confirma** antes de discar | **sim** | liga pro pedro no teams |
| posta / publica / sobe no insta / tuita | publicar | nunca publica sozinho: prepara e pede confirmação | **sim** | posta essa foto |
| compra / finaliza a compra / paga / faz o pix / transfere | comprar / pagar | **nunca sozinho**: leva até o carrinho/tela e o usuário conclui | **sempre o usuário** | compra esse fone |

## Arquivos e pastas

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| cria uma pasta / faz uma pasta / nova pasta | criar pasta | File Agent cria no local citado (padrão: Documentos) | não | cria uma pasta projetos na área de trabalho |
| organiza / arruma / separa / ajeita / põe em ordem | organizar arquivos | File Agent: mostra o plano e move por tipo/data | se mover muitos | arruma a pasta downloads |
| acha / encontra / onde tá / cadê o arquivo | encontrar arquivo | busca por nome/tipo nas pastas do usuário | não | cadê o pdf do contrato |
| renomeia / muda o nome / troca o nome | renomear | File Agent renomeia (mantém extensão) | não | renomeia pra relatorio final |
| move / passa pra pasta / joga na pasta | mover | File Agent move | se muitos arquivos | move as fotos pra pasta viagem |
| compacta / zipa / faz um zip / descompacta / extrai | compactar/extrair | File Agent (zip) | não | zipa essa pasta |
| apaga / deleta / exclui / tira / remove / limpa / joga fora / manda pro lixo | apagar | manda para a **Lixeira**, nunca apaga direto; lista antes | **sim** | apaga os temporários |
| baixa / baixar / faz o download / puxa o arquivo | baixar | download no navegador (pasta Downloads) | se for programa (.exe) | baixa esse pdf |
| sobe / faz upload / anexa / upa | enviar arquivo (upload) | seleciona o arquivo pelo nome; confirma antes de enviar a terceiros | se for para outra pessoa | anexa o relatório no email |

## Criar e alterar

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| cria / crie / faz / faça / monta / gera / bola / desenvolve / programa | criar (site, app, script, planilha, texto) | Code Agent (site/app/script), Data Agent (planilha com dados), Maestro gera o texto | não | faz um site de cafeteria |
| faz uma planilha de / monta uma tabela de / controle de gastos | planilha com dados | Data Agent: xlsx com colunas, fórmulas e gráfico | não | faz uma planilha de gastos do mês |
| muda / troca / altera / ajusta / mexe / dá um tapa / melhora / deixa mais | alterar o que está aberto | continua no alvo da conversa (código: edita com backup; site: navega; doc: edita) | se não disser o quê | troca a cor pra azul |
| adiciona / acrescenta / coloca mais / põe um / inclui | adicionar | no alvo aberto | não | coloca um botão de contato |
| tira / remove / some com / sem o | remover (do conteúdo) | no alvo aberto; em arquivos = apagar (confirma) | se for arquivo | tira o rodapé |
| roda / executa / testa / builda / compila | executar código | Code Agent roda e mostra o resultado | não | roda o script |
| agenda / marca na agenda / coloca no calendário / me lembra | agendar / lembrete | Google Agenda/Outlook; lembrete com data absoluta | não | me lembra de ligar amanhã às 10 |

## Controle da conversa

| Fala | Intenção | Como o agente executa | Confirma? | Exemplo |
|---|---|---|---|---|
| continua / segue / vai / pode ir / manda ver / bora / vamo / prossegue | continuar / pode executar | segue o plano ou aceita a oferta feita | — | pode ir |
| para / pare / chega / cancela / esquece / deixa pra lá / não precisa / aborta | cancelar / parar | interrompe a execução e esvazia a fila | — | esquece, não precisa |
| de novo / outra vez / repete / faz de novo / mais uma vez | repetir a última ação | refaz o último pedido | — | faz de novo |
| repete o que você disse / fala de novo / não ouvi | repetir a fala | repete a última resposta falada | — | fala de novo |
| sim / isso / exato / é isso / pode / pode ser / beleza / fechou / bora / manda / confirmado / quero | confirmação (sim) | executa o que foi oferecido/perguntado | — | pode mandar |
| não / nada / negativo / nem / esquece / deixa / melhor não / errado | negação (não) | descarta o palpite e pede de novo | — | melhor não |
| e depois / em seguida / aí depois / e também / e aí | encadear pedidos | Maestro quebra em subtarefas, na ordem | — | abre o excel e depois o word |
| enquanto isso / ao mesmo tempo | pedido em paralelo | entra na fila; executa ao terminar o atual | — | enquanto isso abre o spotify |
