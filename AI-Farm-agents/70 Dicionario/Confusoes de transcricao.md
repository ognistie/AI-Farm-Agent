---
tipo: dicionario
tags: [dicionario, voz]
cssclasses: [agent-maestro]
atualizado: 2026-10-05
---

# 🎧 Confusões comuns da transcrição

← [[Dicionario de voz]]

> [!info] Uso
> Erros típicos do reconhecimento de voz em português. **Corrigir = auto**: o agente troca **antes** de entender (só para o que nunca é uma palavra normal, como "google escute"). **Corrigir = dica**: vai só como pista para o modelo, que decide pela frase ("ponto", "time", "vê esse código" mudam de sentido). Na dúvida, o agente confirma **uma vez**.
>
> [!tip] Ensine o agente
> Viu uma transcrição errada no balão "Ouvi:"? Acrescente uma linha (`fala errada | certo | motivo | auto ou dica`). Use **auto** só quando a fala errada nunca for dita de propósito.

## Ouvido → Provavelmente

| Fala | Provavelmente | Por quê | Corrigir |
|---|---|---|---|
| google escute / google escuta / vê esse coche / vi es code / vês code / vs cold / vez code / v s code | VS Code | som de 'vê-esse-code' | auto |
| vê esse código | VS Code | som de 'vê-esse-code' — depende da frase | dica |
| o meu meu google / meu meu google / o meu google | o Google | gaguejo + 'meu' de posse | auto |
| you tube / iu tubo / io tubo / iutu | YouTube | pronúncia aportuguesada | auto |
| o tubo | YouTube | pronúncia aportuguesada — depende da frase | dica |
| bloco de nota / bloco de notícias / blog de notas / bloco de nós | Bloco de Notas | som parecido | auto |
| espote fai / spot fy / espoti fai / spotfy | Spotify | pronúncia aportuguesada | auto |
| zap zap / zape / zapi / uatisapi / whats app | WhatsApp | apelido / pronúncia | auto |
| gimeu / gê mail / ji mail | Gmail | pronúncia | auto |
| gemeu | Gmail | pronúncia — depende da frase | dica |
| crome / crômi | Chrome | pronúncia | auto |
| cromo | Chrome | pronúncia — depende da frase | dica |
| eji / édge / edge do windows | Edge | pronúncia | auto |
| exel / ecsel / éxcel / exceu | Excel | pronúncia ('excelente' no fim da frase NÃO é Excel: só o modelo decide) | auto |
| uórdi | Word | pronúncia | auto |
| ord / o word / a word | Word | pronúncia — depende da frase | dica |
| tims | Teams | pronúncia | auto |
| times / time (app de reunião) | Teams | pronúncia — depende da frase | dica |
| configuraçõe / configurações do uindous / ajuste do windows | Configurações do Windows | pronúncia | auto |
| config | Configurações do Windows | pronúncia — depende da frase | dica |
| uindous / uindous / rindous | Windows | pronúncia | auto |
| windows | Windows | pronúncia — depende da frase | dica |
| guiti rábi / git rub / guit hub | GitHub | pronúncia | auto |
| chat gepeto / chat gêpetê / chat jpt | ChatGPT | pronúncia | auto |
| obsidia / ob sidian | Obsidian | pronúncia | auto |
| obsidiana | Obsidian | pronúncia — depende da frase | dica |
| calculadoura | Calculadora | som parecido | auto |
| calculador | Calculadora | som parecido — depende da frase | dica |
| netiflix / net flix / netflics | Netflix | pronúncia | auto |
| mercado livro / mercado libre | Mercado Livre | som parecido | auto |
| ai food / aifud / i food | iFood | pronúncia | auto |
| pê dê efe / pedeefe | PDF | sigla soletrada | auto |
| pdf | PDF | sigla soletrada — depende da frase | dica |
| agá tê eme ele / rtml | HTML | sigla soletrada | auto |
| html | HTML | sigla soletrada — depende da frase | dica |
| cê esse esse | CSS | sigla soletrada | auto |
| css / cs | CSS | sigla soletrada — depende da frase | dica |
| jota esse | JavaScript | sigla soletrada | auto |
| js / javascript / java script | JavaScript | sigla soletrada — depende da frase | dica |
| páiton / paitom | Python | pronúncia | auto |
| python / piton | Python | pronúncia — depende da frase | dica |
| a pê i / ei pi ai | API | sigla | auto |
| api | API | sigla — depende da frase | dica |
| u erre ele | URL | sigla | auto |
| url | URL | sigla — depende da frase | dica |
| uai fai | Wi-Fi | pronúncia | auto |
| wi-fi / wifi | Wi-Fi | pronúncia — depende da frase | dica |
| blutufe / blu tufi | Bluetooth | pronúncia | auto |
| bluetooth | Bluetooth | pronúncia — depende da frase | dica |
| print / prinche / print screen | print (captura de tela) | pronúncia | dica |
| daunlouds / donlouds | Downloads | pronúncia | auto |
| downloads | Downloads | pronúncia — depende da frase | dica |
| desquitópi | Área de Trabalho | pronúncia | auto |
| desktop / área de trabalho | Área de Trabalho | pronúncia — depende da frase | dica |
| dois pontos / barra / ponto com / ponto com ponto br | : / / / .com / .com.br | ditado de endereço | dica |
| arroba | @ | ditado de e-mail | dica |
| underline / underscore / traço baixo | _ | ditado | dica |
| hífen / traço / tracinho | - | ditado | dica |
| nova linha / pula linha / próximo parágrafo | quebra de linha | ditado de texto | dica |
| vírgula / ponto / ponto final / interrogação / exclamação | , . . ? ! | ditado de pontuação | dica |
| configurações do youtube / configuração do youtube / ajustes do youtube | provavelmente 'configurações do Windows' (Windows e YouTube soam parecido): confirmar se não houver YouTube aberto | visto em teste real | dica |
| abru | abre | sotaque / conjugação | auto |
| abre-o | abre | sotaque / conjugação — depende da frase | dica |
| o excel permite / excel permite | provavelmente 'abre o Excel' (frase cortada) | visto em teste real | dica |
| vou para o youtube / vou pro youtube | ir para o YouTube (= abrir o YouTube) | 1ª pessoa no lugar do pedido | dica |
| frases que não combinam com o pedido ('você quer?', 'não tem que dar um pedido de bala') | provável ruído/alucinação da transcrição | descartar e confirmar | dica |
| abri o / abri a / abri meu / abri minha | abre o / abre a / abre meu / abre minha | o reconhecimento escreve o passado 'abri' no lugar do pedido 'abre' | dica |
| note pad / notpad / nôtpad | Bloco de Notas | pronúncia em inglês | auto |
| visual estúdio code / visual studio coud / vs coud | VS Code | pronúncia | auto |
| espotifai / spotfay / spotifai | Spotify | pronúncia aportuguesada | auto |
| uatizap / uatsapi / whatzap | WhatsApp | pronúncia | auto |
| instagran / istagram / insta gram | Instagram | pronúncia | auto |
| linquedim / linkedim / link edin | LinkedIn | pronúncia | auto |
| pauer point / power poin / pauerpoin | PowerPoint | pronúncia | auto |
| pauer bi ai / power bi ai | Power BI | pronúncia | auto |
| aut luque / autlook / out look | Outlook | pronúncia | auto |
| tins / tímis | Teams | pronúncia | auto |
| discordi / dis cord | Discord | pronúncia | auto |
| jimeil / gi meil / gê meio | Gmail | pronúncia | auto |
| iutúbi / iútubi / you tubi | YouTube | pronúncia | auto |
| gugou xrome / google crome | Google Chrome | pronúncia | auto |
| efe cinco / f cinco | F5 | tecla soletrada | auto |
| efe onze / f onze | F11 | tecla soletrada | auto |
| contrôu cê / control c / controle c | Ctrl+C | atalho falado | dica |
| contrôu vê / control v / controle v | Ctrl+V | atalho falado | dica |
| contrôu zê / control z / controle z | Ctrl+Z | atalho falado | dica |
| ênter / enter | Enter | tecla | dica |
| delíti / dilete | Delete | tecla | auto |
| tébi / tab | Tab | tecla | dica |
| minimisa / minimisar | minimiza | grafia | auto |
| maximisa / maximisar | maximiza | grafia | auto |
| pesquisa no gugou / pesquisa no gúgol | pesquisa no Google | pronúncia | auto |
| célula a um / célula a1 / a um | célula A1 | referência de planilha falada | dica |
| bê dois / be dois | B2 | referência de planilha falada | dica |
| coluna á / coluna bê / coluna cê | coluna A / B / C | letra falada | dica |
| ponto com ponto bê erre / ponto com br | .com.br | ditado de endereço | dica |
| três dáblio / dáblio dáblio dáblio | www | ditado de endereço | dica |
| abre as configurações do iutubi / configuração do iutube | provavelmente 'configurações do Windows' — confirmar se não houver YouTube aberto | Windows e YouTube soam parecido | dica |
| vou pro google / vou no google / vou abrir o google | abrir o Google (1ª pessoa no lugar do pedido) | jeito de falar | dica |
| 'legendas pela comunidade amara.org' / 'obrigado por assistir' / 'inscreva-se' | frase fantasma do reconhecimento em silêncio: descartar | alucinação conhecida do Whisper | dica |
| frase cortada: 'abre o...' / 'pesquisa...' / 'clica no...' | pedido incompleto: perguntar UMA vez o que falta | fala cortada pela pausa | dica |
