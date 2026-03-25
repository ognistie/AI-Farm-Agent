_<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Claude_API-Anthropic-purple?style=for-the-badge&logo=anthropic&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-SocketIO-black?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Playwright-Browser-green?style=for-the-badge&logo=playwright&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
</p>

<h1 align="center">⚡ AI Agent Farm</h1>

<p align="center">
  <b>Um agente de IA que executa tarefas no seu computador como se fosse uma pessoa sentada na sua frente.</b><br>
  Descreva o que precisa em linguagem natural — ele planeja, executa e documenta tudo.
</p>

<p align="center">
  <a href="https://github.com/ognistie">Desenvolvido por @ognistie</a>
</p>

---

## 🎯 O que é o AI Farm Agent?

O AI Farm Agent é um sistema de automação inteligente que transforma comandos em linguagem natural em ações reais no seu computador. Ele funciona como um assistente que:

- **Entende** o que você pede em português natural
- **Planeja** a melhor sequência de ações para executar
- **Executa** as ações no seu PC (abrir apps, criar arquivos, navegar na web, preencher planilhas)
- **Documenta** tudo com screenshots e gera relatórios educacionais

A diferença de outros assistentes é que o AI Farm Agent **age no seu computador de verdade** — abre programas, digita texto, clica em botões, cria arquivos, navega na internet. Como um TeamViewer onde quem controla é uma IA.

---

## 🧠 Como funciona

```
Usuário digita: "Crie uma planilha no Excel com dados de vendas"
         │
         ▼
┌─────────────────────────┐
│   🧠 IA PLANEJADORA     │  Claude API analisa o pedido e gera
│   (Claude Sonnet 4)      │  um plano de ações estruturado (JSON)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│   ⚙️ MOTOR DE AUTOMAÇÃO  │  Executa cada ação no PC:
│   Smart Actions          │  • excel_write → cria planilha por código
│   + Vision + Playwright  │  • app_search → abre apps pelo menu Iniciar
│   + PyAutoGUI            │  • vision_click → IA vê a tela e clica
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│   📸 CAPTURA DE TELA     │  Screenshots anotados a cada passo
│   + Relatório Educativo  │  + relatório estilo "skill builder"
└─────────────────────────┘
```

### Fluxo detalhado

1. O usuário digita um pedido em linguagem natural na interface web
2. A **IA Planejadora** (Claude API) converte o pedido em um plano de ações JSON
3. O **Motor de Automação** escolhe a melhor ferramenta para cada ação:
   - **Automação direta** (código) para Excel, arquivos, terminal — mais rápido e confiável
   - **Playwright** para navegação web — controle total do browser sem depender de pixels
   - **Visão Computacional** (Claude Vision) para apps desktop — quando precisa "ver" a tela
   - **PyAutoGUI** para mouse/teclado — quando precisa interagir com interface nativa
4. O **Sistema de Captura** tira screenshots anotados a cada passo
5. A **IA Narradora** gera um relatório educacional explicando o que foi feito

---

## 🛠️ Stack Técnica

### Backend

| Tecnologia | Função |
|---|---|
| **Python 3.11+** | Linguagem principal do projeto |
| **Flask + SocketIO** | Servidor web com comunicação em tempo real via WebSocket |
| **Anthropic Claude API** | Cérebro do sistema — planejamento, visão computacional e geração de relatórios |

### Automação

| Tecnologia | Função |
|---|---|
| **PyAutoGUI** | Controle de mouse e teclado para interação com apps desktop |
| **Playwright** | Controle programático do browser Chrome — navegação web confiável |
| **PyGetWindow** | Gerenciamento de janelas do Windows — foco, minimizar, restaurar |
| **openpyxl** | Criação e edição de planilhas Excel diretamente por código |
| **Pillow** | Processamento de imagens e anotação de screenshots |
| **psutil** | Monitoramento de processos do sistema |

### Frontend

| Tecnologia | Função |
|---|---|
| **HTML5 + CSS3** | Interface futurista com gradientes, glassmorphism e animações |
| **JavaScript (Vanilla)** | State management, WebSocket client, renderização dinâmica |
| **Socket.IO Client** | Comunicação em tempo real com o servidor |

### IA — Papel no Projeto

A IA (Claude da Anthropic) tem **3 papéis distintos**:

| Papel | Modelo | O que faz |
|---|---|---|
| **Planejador** | Claude Sonnet 4 | Recebe pedido em linguagem natural → gera plano de ações JSON |
| **Visão** | Claude Sonnet 4 (Vision) | Recebe screenshot da tela → identifica elementos visuais e suas coordenadas |
| **Narrador** | Claude Sonnet 4 | Recebe logs de execução → gera relatório educacional estilo skill-builder |

---

## 📂 Estrutura do Projeto

```
ai-farm-agent/
├── main.py                    # Ponto de entrada — carrega .env, inicia servidor
├── requirements.txt           # Dependências Python
├── .env                       # Chave da API Anthropic
│
├── core/                      # Módulos do backend
│   ├── __init__.py
│   ├── planner.py             # IA Planejadora — converte linguagem natural → JSON
│   ├── automation.py          # Motor de Automação — executa ações no PC
│   ├── vision.py              # Visão Computacional — IA que "vê" a tela
│   ├── capture.py             # Sistema de Captura — screenshots anotados
│   └── narrator.py            # IA Narradora — gera relatórios educacionais
│
├── ui/                        # Interface web
│   ├── server.py              # Flask + SocketIO — rotas e pipeline
│   ├── templates/
│   │   └── index.html         # Página principal
│   └── static/
│       ├── css/style.css      # Estilo futurista
│       └── js/app.js          # Lógica do frontend
│
├── captures/                  # Screenshots salvos automaticamente
└── reports/                   # Relatórios JSON gerados
```

---

## ⚡ Ações Disponíveis

### 🧠 Ações Inteligentes (automação direta por código)

| Ação | Descrição | Exemplo |
|---|---|---|
| `excel_write` | Cria planilha Excel sem clicar em células | Dados tabulares, relatórios |
| `app_search` | Abre qualquer app pelo menu Iniciar | "Excel", "Teams", "VS Code" |
| `app_type` | Encontra janela, foca e digita texto | Escrever no Notepad, chat |

### 🌐 Web (Playwright)

| Ação | Descrição |
|---|---|
| `web_goto` | Navega para URL (abre browser automaticamente) |
| `web_type` | Digita em campo de formulário |
| `web_click` | Clica em elemento por texto |
| `web_key` | Pressiona tecla (Enter, Tab) |
| `web_read` | Lê conteúdo da página |

### 👁️ Visão Computacional (Claude Vision)

| Ação | Descrição |
|---|---|
| `vision_click` | IA vê a tela e clica no elemento descrito |
| `vision_type` | IA encontra campo visual, clica e digita |
| `vision_smart` | IA decide a melhor ação sozinha |

### 📁 Arquivos

| Ação | Descrição |
|---|---|
| `create_folder` | Cria pasta |
| `write_file` | Cria/escreve arquivo |
| `move_file` | Move arquivo |
| `list_files` | Lista conteúdo de diretório |
| `find_files` | Busca por padrão (*.pdf, *.py) |
| `run_command` | Executa comando no terminal |

---

## 🚀 Instalação

### Pré-requisitos

- Windows 10/11
- Python 3.11 ou superior
- Chave da API Anthropic ([console.anthropic.com](https://console.anthropic.com))

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/ognistie/AI-Farm-Agent.git
cd AI-Farm-Agent

# 2. Instale as dependências
pip install -r requirements.txt
pip install openpyxl

# 3. Instale o Playwright (para automação web)
pip install playwright
python -m playwright install chromium

# 4. Configure a API Key
# Edite o arquivo .env e cole sua chave:
# ANTHROPIC_API_KEY=sk-ant-SUA_CHAVE_AQUI

# 5. Execute
python main.py
```

O browser abre automaticamente em `http://127.0.0.1:5000`.

---

## 💡 Exemplos de uso

| Comando | O que acontece |
|---|---|
| "Organize meus Downloads por tipo" | Lista arquivos, cria pastas por extensão, move cada arquivo |
| "Crie uma planilha com dados de vendas" | Gera .xlsx com openpyxl e abre no Excel |
| "Pesquise no Google como usar Git" | Abre browser, navega ao Google, pesquisa |
| "Abra o Notepad e escreva um poema" | Abre Bloco de Notas, foca a janela, digita |
| "Mande mensagem no Teams para João" | Abre Teams, navega ao chat, digita e envia |
| "Crie um site com HTML e CSS no VS Code" | Cria arquivos, abre no VS Code |

---

## 🏗️ Arquitetura

```
┌──────────────┐     WebSocket      ┌──────────────┐
│   Frontend   │◄──────────────────►│   Flask +    │
│   (Browser)  │   Tempo real       │   SocketIO   │
└──────────────┘                    └──────┬───────┘
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                        ┌──────────┐ ┌──────────┐ ┌──────────┐
                        │ Planner  │ │  Engine  │ │ Narrator │
                        │(Claude)  │ │(Actions) │ │(Claude)  │
                        └──────────┘ └────┬─────┘ └──────────┘
                                          │
                           ┌──────────────┼──────────────┐
                           ▼              ▼              ▼
                     ┌──────────┐  ┌──────────┐  ┌──────────┐
                     │ Smart    │  │Playwright│  │  Vision  │
                     │ Actions  │  │ (Web)    │  │ (Claude) │
                     │(Excel,   │  │          │  │          │
                     │ Files)   │  │          │  │          │
                     └──────────┘  └──────────┘  └──────────┘
```

---

## 🔒 Segurança

- Comandos perigosos são bloqueados (`rm -rf`, `format`, `shutdown`, etc.)
- PyAutoGUI FailSafe ativado (mover mouse para canto = para tudo)
- Coordenadas clampadas para nunca disparar FailSafe acidentalmente
- O agente verifica foco da janela antes de digitar para não enviar texto no lugar errado

---

## 📄 Licença

Este projeto é de código aberto. Desenvolvido por [@ognistie](https://github.com/ognistie).

---

<p align="center">
  <b>⚡ AI Farm Agent — Automação inteligente para o dia a dia.</b>
</p>
_ 
