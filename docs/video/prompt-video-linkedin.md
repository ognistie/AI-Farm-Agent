# Prompt — Vídeo de lançamento do AI Farm Agent (LinkedIn)

> Cole tudo abaixo da linha no Claude Design. Antes, anexe os arquivos da seção **Materiais anexados** e preencha os campos marcados com `⟦ ⟧`.

---

## 0. Seu papel

Você é diretor criativo e motion designer de filmes de produto no nível da Apple (keynotes e páginas de produto), da Anthropic (lançamentos do Claude) e da OpenAI (demos de lançamento). Sua tarefa é criar **um filme de produto de 80 a 90 segundos** para o LinkedIn sobre o **AI Farm Agent**, um projeto open source.

O filme precisa parecer feito por uma equipe de produto, **não por uma IA**. O critério de sucesso: quem rola o feed do LinkedIn para no primeiro segundo, entende o produto sem som e termina o vídeo querendo testar.

Esta é a **segunda versão**. A primeira tinha três problemas, que esta versão precisa resolver (detalhes na seção 9):
1. **Informação demais.** Muito texto, muitos conceitos por cena.
2. **Telas abstratas.** Partes do vídeo mostravam diagramas e telas genéricas em vez do computador de verdade.
3. **Pouca ação real.** Faltou ver o agente abrindo apps, clicando e digitando num desktop.

---

## 1. O que é o produto (leia antes de criar)

**AI Farm Agent** é um assistente que **opera o computador por você**. A pessoa descreve o que quer, por texto ou por voz, em português do jeito que fala no dia a dia, e o agente executa no desktop: abre aplicativos, navega na web, clica, digita, cria planilhas, gera sites e organiza arquivos.

Por dentro:

- **Maestro (orquestrador).** Entende o pedido, divide em subtarefas e escolhe o agente certo para cada uma.
- **Seis agentes especialistas:** Web, Desktop, Code, Data (planilhas), File (arquivos) e Memória. Cada um tem **3 ajudantes**: *Entender* o pedido → *Montar* a execução → *Conferir* antes de agir. **14 dos 15 ajudantes não usam IA** (são código determinístico, custo zero).
- **Harness de validação.** *"Quem propõe não aprova o próprio plano."* Todo plano passa por políticas de aceite em código antes de tocar no computador. Se for reprovado, o Maestro replaneja uma vez com o motivo exato.
- **Segundo cérebro (Obsidian).** Uma base de conhecimento com 370+ notas interligadas: regras de cada agente, playbooks, tarefas de referência, lições aprendidas e um dicionário de como o brasileiro fala. **Antes de agir**, cada agente consulta o cérebro. **Depois de agir**, o app escreve no cérebro o plano, a validação e o resultado. Para ensinar algo novo ao agente, basta escrever uma nota.
- **Conversa contínua.** O agente lembra o que fez e o que ficou aberto. Entende "agora", "esse", "o segundo", "desfaz".
- **Voz.** Atalho global, transcrição **local** (no próprio PC), dicionário com ~2.600 jeitos de falar (gírias, apelidos de apps, erros de transcrição) e voz neural **local** em português. Exemplo real: o transcritor ouve *"abre o google escute"* e o agente entende **"abrir o VS Code"**.
- **Custo.** Tudo que pode rodar local roda local (voz, transcrição, OCR, ajudantes, rotinas simples). O modelo só é chamado onde precisa raciocinar, com cache de prompt e esforço calibrado por agente. Resultado do nosso benchmark: **até 11× mais barato** que ChatGPT Work (OpenAI) e Claude Cowork (Anthropic) ⟦confirmar nomes exatos dos produtos⟧.

**Visão / ambição:** um assistente de computador que qualquer pessoa usa falando normalmente, que melhora porque aprende com o que executa, e que é barato o bastante para rodar o dia inteiro. Open source, licença MIT.

**Público do vídeo:** profissionais de tecnologia, produto e negócios no LinkedIn: devs, fundadores, gestores, recrutadores e entusiastas de IA.

---

## 2. Direção criativa

### Conceito
**"Você pede. Ele faz."**

O filme inteiro é construído sobre um único gesto: uma frase curta vira uma ação real na tela. Sem explicar demais: **mostrar**. A tecnologia (harness, cérebro, custo) só aparece *depois* que o espectador já viu o produto funcionando e quer saber como.

### Referências de estilo
⟦Se você conseguir acessar, assista às referências: https://lnkd.in/p/gw6sgNne · https://lnkd.in/p/gr7MP9qH · https://www.youtube.com/watch?v=UAmKyyZ-b9E⟧
⟦Descreva aqui em 1–2 linhas o que você gostou em cada uma: ritmo, transições, tipografia, enquadramento⟧

Adapte destas referências a **linguagem**, não o conteúdo:

- **Apple:** uma ideia por plano, muito respiro, tipografia grande e curta, câmera que desliza devagar sobre a tela, cortes no tempo da música.
- **Anthropic:** calma, tons quentes e neutros, texto como protagonista, nada de efeito chamativo, confiança sem exagero.
- **OpenAI (demos):** tela real, ação real, a sensação de "isso está acontecendo agora", cursor e digitação visíveis.

### Regras visuais
- **A tela é a estrela.** Pelo menos 60% do tempo mostra o desktop com o agente agindo. Os gráficos explicativos existem só para as seções de harness, cérebro e custo.
- **Uma ideia por cena. No máximo 6 palavras de texto na tela ao mesmo tempo.** Fora as legendas.
- **Câmera virtual:** zoom suave (ease-in-out, 600–900 ms) no ponto onde a ação acontece: o campo de busca, o vídeo clicado, a célula do Excel. Depois volta ao plano geral. Nunca tremido, nunca rápido demais.
- **Cursor visível**, com movimento natural (curvas, leve desaceleração no alvo) e um anel sutil no clique.
- **Digitação real**, letra por letra, num ritmo humano (~12 caracteres/s), com pausa curta antes do Enter.
- **Profundidade:** a janela do app flutua sobre o wallpaper com sombra suave. Nada de mockup 3D girando.
- **Transições:** cortes secos no tempo da música, *match cuts* (o campo de texto do app vira o título da próxima cena) e zoom contínuo (entrar na tela → virar diagrama). Sem wipes, sem glitch, sem transições "tech".

### Paleta (vem do próprio produto)
| Uso | Cor |
|---|---|
| Fundo base | `#1E1E1F` |
| Barra lateral / fundos mais escuros | `#171717` |
| Superfície (cards, composer) | `#262628` |
| Texto principal | `#ECECEC` |
| Texto secundário | `#A1A1A6` |
| Sucesso | `#30D158` |
| Destaque do Maestro | `#F97316` (laranja) |

Cores dos agentes (as mesmas do grafo do Obsidian; use-as sempre que um agente aparecer):

| Agente / área | Cor |
|---|---|
| Maestro | `#F97316` laranja |
| Web | `#38BDF8` azul-céu |
| Desktop | `#FBBF24` âmbar |
| Code | `#34D399` verde-esmeralda |
| Data | `#A78BFA` violeta |
| File | `#FB923C` laranja-claro |
| Memória | `#94A3B8` cinza-ardósia |
| Políticas | `#EF4444` vermelho |
| Tarefas de referência | `#FDE68A` amarelo-claro |
| Execuções com sucesso | `#22C55E` verde |
| Lições aprendidas | `#2DD4BF` turquesa |

### Tipografia
- Títulos: sans-serif display, peso semibold, tracking levemente negativo (Inter Display, SF Pro Display ou Segoe UI Variable Display).
- Corpo e legendas: mesma família, peso regular.
- Código e termos técnicos (raros): Cascadia Mono ou JetBrains Mono.
- Títulos em frase curta, **sem ponto de exclamação**, sem CAIXA ALTA.

### Som
- **Trilha:** minimalista e moderna. Piano ou sintetizador limpo com um pulso que cresce aos poucos, ~100–110 BPM. Silêncio estratégico no hook e antes do número de custo.
- **Efeitos sonoros discretos:** teclado mecânico suave, clique de mouse leve, um "tick" sutil quando um passo é concluído.
- **Narração:** opcional. Se houver, voz humana em PT-BR, calma, frases de no máximo 8 palavras. Na cena de voz, a **voz do próprio agente** aparece de verdade (diegética), não como narração.
- **O vídeo precisa funcionar sem som:** o LinkedIn toca no mudo. Legendas queimadas em PT-BR em todas as falas.

### Formato
- Master **1920×1080 (16:9), 30 fps**, H.264, 80–90 s.
- Versão alternativa **1080×1350 (4:5)** para o feed: a janela do desktop centralizada, com o texto acima e as legendas abaixo.
- Margens de segurança: nada importante a menos de 80 px das bordas.

---

## 3. O desktop (ambiente das demos)

> ⚠️ **Plataforma:** o AI Farm Agent hoje roda em **Windows 10/11** (usa a automação nativa do Windows). Mostrar o produto num Mac passaria uma informação falsa no post. Use um **Windows 11 limpo, com estética premium**: modo escuro, wallpaper minimalista (gradiente escuro quente e liso, sem paisagem genérica), barra de tarefas centralizada só com os apps da cena, **nenhum ícone na área de trabalho**, sem notificações e sem marcas de ativação. O enquadramento é a tela inteira, ou a tela dentro de um monitor/notebook neutro e sem logo em plano aberto.
> ⟦Se o produto ganhar suporte a macOS antes do lançamento, troque por um macOS Sequoia limpo e apague este aviso.⟧

- **Use as gravações de tela reais** anexadas sempre que existirem. Onde não houver gravação, **recrie a interface fielmente** a partir dos screenshots anexados (`desktop-interface.png`), com a paleta e a tipografia acima. Não invente telas que o produto não tem.
- Interface do AI Farm Agent: barra lateral escura à esquerda ("Nova conversa", "Histórico", "Sobre", lista de conversas recentes), título central *"O que você quer que eu faça?"* e composer arredondado com os botões **Simular** e **Relatório**, o microfone e o botão de enviar. No rodapé, o status: `● Pronto · Claude Sonnet 5`.
- Durante uma tarefa o app mostra uma **transcrição ao vivo**: "Entendi: …", o plano, cada passo com status (spinner → ✓ verde) e, no fim, uma resposta curta e natural do assistente ("Feito! Abri o segundo vídeo.").
- Layout das demos: o **AI Farm Agent ocupa uma coluna estreita à direita** (~30% da tela) e o app sendo operado (navegador, Excel, VS Code) ocupa o resto. Assim o espectador vê o pedido e a ação **ao mesmo tempo**.
- Dados de exemplo **fictícios e neutros**: nada de e-mails, nomes ou contas reais na tela.

---

## 4. Roteiro (plano a plano)

Tempo total alvo: **~88 s**. Texto entre aspas `" "` é o que aparece digitado ou falado na tela. **TEXTO NA TELA** é a tipografia sobreposta.

### CENA 1 — Hook (0:00–0:05)
- **Visual:** tela preta. Um cursor de texto pisca no centro. Digitação: `"abre meu YouTube"`. Enter. **Corte seco** para o desktop: o navegador abre sozinho, o YouTube carrega. O cursor do mouse se move sem ninguém tocar nele.
- **TEXTO NA TELA:** *Você pede.* → (no clique) *Ele faz.*
- **Som:** silêncio. Só as teclas. A música entra no corte.
- **Objetivo:** em 3 segundos o espectador entende o produto sem ler nada.

### CENA 2 — Conversa contínua por texto (0:05–0:22)
Sequência encadeada **na mesma janela**, sem cortes que escondam a ação:
1. Composer: `"pesquisa lofi para estudar"` → o agente clica no campo de busca do YouTube, digita e dá Enter. A grade de vídeos aparece.
2. Composer: `"agora clica no segundo vídeo"` → zoom suave na grade, o **segundo** card ganha um contorno de destaque (azul Web `#38BDF8`) e o cursor clica. O vídeo abre.
3. Composer: `"qual era o nome do primeiro?"` → **nada acontece na tela do navegador**. O assistente só responde no chat com o título. (Mostra que ele lembra o contexto e sabe quando *não* agir.)
- Na coluna do app, cada pedido aparece como "Entendi: abrir o 2º vídeo da pesquisa no YouTube" e um ✓ verde.
- **TEXTO NA TELA (só uma vez, no passo 2):** *Ele lembra do contexto.*

### CENA 3 — Voz, mãos livres (0:22–0:38)
- **Visual:** a pessoa ativa a **Conversa ao vivo** (toggle no app; atalho `Ctrl+Alt+V` aparece como uma tecla discreta). Uma onda sonora fina e elegante pulsa no composer.
- **Fala 1 (legendada):** *"abre o VS Code"*
  - Detalhe "uau", em zoom: a linha **"Ouvi: abre o google escute"** aparece e, um instante depois, se transforma (morph de texto) em **"Entendi: abrir o VS Code"**.
  - Voz do agente (áudio real, voz neural local): *"Abrindo o VS Code."* O VS Code abre.
- **Fala 2:** *"abre o Excel e preenche a coluna A com os meses do ano"*
  - Voz do agente: *"Bora, abrindo o Excel."* O Excel abre e as células A1→A12 são preenchidas uma a uma, **de Janeiro a Dezembro**, com a câmera acompanhando.
- **Fala 3:** *"salva essa planilha como vendas"* → caixa de salvar → `vendas.xlsx` → ✓.
- **TEXTO NA TELA:** *Fale do seu jeito.* (pequeno, canto inferior, entra na fala 1 e sai na fala 2)
- **Legenda de rodapé (pequena, 2 s):** *Transcrição e voz rodando no seu PC.*

### CENA 4 — O pedido mais ousado (0:38–0:50)
- **Composer:** `"crie um site sobre uma floricultura"`
- **Visual:** o VS Code se enche de arquivos (`index.html`, `style.css`, `script.js`) em sequência rápida. O navegador abre o site pronto: bonito, com hero, cores suaves e fotos de flores em placeholder elegante.
- **Composer:** `"troca a cor principal para azul"` → o site **muda de cor ao vivo** com uma transição suave.
- **Composer:** `"desfaz"` → volta para a cor original.
- **TEXTO NA TELA:** *Criar. Ajustar. Desfazer.*

### CENA 5 — Como funciona: o harness (0:50–1:02)
- **Transição:** zoom contínuo *para dentro* do composer. O pedido `"pesquisa o preço do dólar e anota no bloco de notas"` se solta da tela e vira um card flutuando no escuro.
- **Visual (diagrama vivo, minimalista, linhas finas de 1.5 px):**
  1. O card chega ao **Maestro** (nó laranja `#F97316`), que o **divide** em 2 subtarefas.
  2. Cada subtarefa voa para o seu agente: **Web** (azul) e **Desktop** (âmbar). Os outros agentes (Code, Data, File, Memória) ficam visíveis, porém apagados.
  3. Dentro de cada agente, três pontos acendem em sequência: **Entender → Montar → Conferir**.
  4. Antes da execução, o plano passa por um **portão de validação** (linha vertical vermelha `#EF4444` com um selo "Políticas de aceite"). Um plano é **reprovado** (o portão fica vermelho), volta ao Maestro e é replanejado, e passa (✓ verde).
  5. O resultado da Web (`R$ 5,⟦xx⟧`) **flui como contexto** até o Desktop, que abre o Bloco de Notas e escreve o valor. Corte rápido para o desktop real mostrando o texto escrito.
- **TEXTO NA TELA (um por vez):** *Um maestro.* → *Agentes especialistas.* → *Nenhum plano executa sem validação.*

### CENA 6 — O segundo cérebro (1:02–1:16) — cena de destaque
Use o **grafo real do Obsidian anexado** (`second-brain.png` / gravação do grafo) como base visual: clusters coloridos de pontos amarelo-claros (tarefas de referência) em volta de nós grandes por agente, com o Maestro laranja no centro.

- **Abertura:** a câmera atravessa o escuro e o grafo **se forma**: os nós surgem do centro para fora e as ligações se desenham como fios finos. Leve paralaxe 2.5D: os nós mais próximos se movem um pouco mais rápido que os de trás.
- **Acionamento 1:** um pedido entra pela esquerda, `"crie uma planilha de gastos com gráfico"`. Um pulso de luz sai do **Maestro**, percorre as arestas e acende em sequência:
  - o nó **Data Agent** (violeta);
  - o playbook **"Planilha com gráfico"** (rótulo aparece ao lado do nó);
  - uma **tarefa de referência** (amarelo);
  - uma **lição aprendida** (turquesa).
  Os rótulos aparecem como mini-cards no estilo do Obsidian (fundo `#262628`, texto pequeno) e somem depois de ~1 s.
- **Micro-corte (2 s):** a planilha real abre no Excel com o gráfico pronto.
- **Volta ao grafo:** um **novo nó verde** (`#22C55E`, "Sucesso") nasce na borda e se conecta ao cluster de Data. O grafo cresceu.
- **Acionamento 2 (rápido, 2 s):** a frase falada *"abre o espotifai"* → um pulso acende o nó do **Dicionário** → rótulo *"espotifai → Spotify"*.
- **Fechamento:** zoom out lento mostrando o grafo inteiro, maior e mais denso do que no começo.
- **TEXTO NA TELA (um por vez):** *Ele consulta antes de agir.* → *E aprende depois.*
- **Legenda pequena:** *370+ notas que você também pode editar.*

### CENA 7 — Custo (1:16–1:26)
- **Visual:** fundo limpo `#1E1E1F`. Três colunas lado a lado, cada uma com o **logo oficial e um screenshot pequeno** da ferramenta:
  - **ChatGPT Work** (OpenAI) · ⟦custo do benchmark⟧
  - **Claude Cowork** (Anthropic) · ⟦custo do benchmark⟧
  - **AI Farm Agent** · ⟦custo do benchmark⟧
- Barras horizontais crescem da esquerda: as duas primeiras longas (cinza `#6E6E73`), a do AI Farm Agent **curta e branca**. Um contador sobe até o número.
- Um beat de **silêncio na música** e então, grande, no centro:
  **TEXTO NA TELA:** *Até 11× mais barato.*
- Abaixo, em 3 linhas pequenas que entram uma por vez (o "por quê"):
  - *Voz e transcrição rodam no seu PC.*
  - *14 de 15 ajudantes sem IA.*
  - *IA só onde precisa pensar.*
- **Rodapé obrigatório (pequeno, legível por 3 s):** *Benchmark próprio, ⟦data⟧, ⟦N tarefas⟧, ⟦metodologia em 1 linha⟧. Preços públicos consultados em ⟦data⟧.*

### CENA 8 — Fechamento (1:26–1:30)
- **Visual:** match cut. O composer do app aparece vazio no centro da tela preta, com o cursor piscando, igual ao hook. Ele se transforma no logo hexagonal do AI Farm Agent.
- **TEXTO NA TELA:**
  - **AI Farm Agent**
  - *Você pede. Ele faz.*
  - pequeno: *Open source · github.com/ognistie/AI-Farm-Agent*
- **Som:** a música resolve num acorde final e termina com uma tecla de Enter.

---

## 5. Tabela de referência rápida

| # | Tempo | Cena | Ação na tela | Texto sobreposto |
|---|---|---|---|---|
| 1 | 0:00–0:05 | Hook | "abre meu YouTube" → navegador abre | Você pede. / Ele faz. |
| 2 | 0:05–0:22 | Conversa contínua | pesquisa → "agora clica no segundo vídeo" → pergunta | Ele lembra do contexto. |
| 3 | 0:22–0:38 | Voz | "google escute" → VS Code; Excel com os meses; salvar | Fale do seu jeito. |
| 4 | 0:38–0:50 | Site | gera site → troca cor → desfaz | Criar. Ajustar. Desfazer. |
| 5 | 0:50–1:02 | Harness | Maestro → agentes → validação → execução | Um maestro. / … / Nenhum plano executa sem validação. |
| 6 | 1:02–1:16 | Segundo cérebro | grafo acende, consulta, novo nó nasce | Ele consulta antes de agir. / E aprende depois. |
| 7 | 1:16–1:26 | Custo | barras comparativas + 3 motivos | Até 11× mais barato. |
| 8 | 1:26–1:30 | Fechamento | composer → logo | AI Farm Agent · Você pede. Ele faz. |

---

## 6. O que NÃO fazer (anti-"vídeo de IA")

- ❌ Cérebros brilhantes, robôs, mãos robóticas, rostos holográficos, circuitos, chuva de código estilo Matrix, túneis de partículas, HUD futurista, lens flare, glitch.
- ❌ Imagens de banco: pessoas sorrindo para o notebook, apontando para telas, escritórios genéricos.
- ❌ Gradientes neon roxo/azul "padrão IA". A paleta é a da seção 2.
- ❌ Palavras vazias: "revolucionário", "o futuro chegou", "nunca foi tão fácil", "game changer", "poder da IA".
- ❌ Muitos textos ao mesmo tempo, bullet points na tela, parágrafos.
- ❌ Telas inventadas ou genéricas no lugar do produto real. Se não existe no app, não aparece.
- ❌ Narração robótica ou TTS genérico em inglês.
- ❌ Emojis na tela.
- ❌ Diagramas com mais de 6 elementos visíveis ao mesmo tempo.
- ❌ Ação escondida por corte: quando o agente clica ou digita, o espectador **vê** acontecer.

---

## 7. Regras de veracidade (obrigatório)

- Mostre **apenas o que o produto faz hoje**. Os exemplos do roteiro vêm dos cenários de teste do projeto. A tela mostrada deve corresponder a uma execução real gravada.
- O produto é **experimental e open source**. Não use "perfeito", "100% seguro" ou "substitui pessoas".
- Os números de custo vêm **exclusivamente** do benchmark anexado. Não arredonde para cima e não invente preços dos concorrentes.
- Logos e screenshots de **OpenAI / ChatGPT** e **Anthropic / Claude** só como **referência comparativa factual**: logo oficial sem distorção, sem sugerir parceria ou endosso, e com fonte e data no rodapé.
- Os dados exibidos (planilhas, nomes, valores) são fictícios.

---

## 8. Materiais anexados

| Arquivo | Uso |
|---|---|
| `desktop-interface.png` | Interface real do app (recriar com fidelidade) |
| `second-brain.png` | Grafo real do Obsidian, base da cena 6 |
| ⟦gravação: YouTube + segundo vídeo⟧ | Cena 1 e 2 |
| ⟦gravação: voz + VS Code + Excel⟧ | Cena 3 |
| ⟦gravação: site floricultura + cor + desfaz⟧ | Cena 4 |
| ⟦gravação: dólar → bloco de notas⟧ | Cena 5 (trecho final) |
| ⟦gravação do grafo do Obsidian em movimento⟧ | Cena 6 |
| ⟦benchmark comparativo: planilha ou imagem⟧ | Cena 7 |
| ⟦logos e screenshots oficiais: ChatGPT Work, Claude Cowork⟧ | Cena 7 |
| ⟦logo hexagonal do AI Farm Agent em SVG/PNG⟧ | Cena 8 |
| ⟦áudio da voz do agente (Piper "cadu")⟧ | Cena 3 |

---

## 9. Correções em relação à versão anterior

1. **Menos informação.** No máximo 6 palavras de texto por vez. Uma ideia por cena. Os detalhes técnicos ficam no post, não no vídeo.
2. **Computador de verdade.** Todos os exemplos acontecem num desktop real, com cursor, janelas e digitação. Nada de telas abstratas para representar uma tarefa.
3. **Tarefas encadeadas.** Pelo menos três sequências contínuas na mesma janela ("abre o YouTube" → "agora clica no segundo vídeo"; "abre o Excel" → "salva como vendas"; "cria o site" → "troca a cor" → "desfaz").
4. **Exemplos novos.** VS Code por voz com a correção "google escute", Excel preenchido por voz, site criado e editado ao vivo, dólar → Bloco de Notas.
5. ⟦Descreva a parte da versão anterior que você não gostou (foto 1) e o que deve ser feito no lugar⟧
6. ⟦Descreva a parte que ficou pouco intuitiva (foto 2). Ela deve ser refeita com imagens reais do computador⟧

---

## 10. Entregáveis

1. Vídeo master 16:9, 1920×1080, 30 fps, 80–90 s, com legendas PT-BR queimadas.
2. Versão 4:5 (1080×1350) para o feed do LinkedIn.
3. Arquivo de legendas `.srt` separado.
4. Thumbnail 1200×627: o composer com `"abre meu YouTube"` e o texto *Você pede. Ele faz.*
5. Antes de renderizar, um **storyboard com 1 quadro por cena** para aprovação.
