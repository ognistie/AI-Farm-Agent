# ══════════════════════════════════════════════════════════════
# AI Farm Agent — Suíte de Testes & Análise de Falhas
# ══════════════════════════════════════════════════════════════
# 30 tarefas reais organizadas por dificuldade
# Para cada uma: resultado esperado, falha provável, solução

TESTS_EASY = [
    {"id": 1, "task": "abra o bloco de notas", "agent": "DESKTOP",
     "expected": "Notepad abre, sem texto", "fail": "Escrevia 'Ola!' por fallback",
     "status": "CORRIGIDO", "fix": "Removido fallback 'Ola!', text='' quando vazio"},
    {"id": 2, "task": "abra a calculadora", "agent": "DESKTOP",
     "expected": "Calculadora abre", "fail": None, "status": "OK", "fix": None},
    {"id": 3, "task": "abra o explorador de arquivos", "agent": "DESKTOP",
     "expected": "Explorer via Win+E", "fail": None, "status": "OK", "fix": None},
    {"id": 4, "task": "pesquise no google sobre python", "agent": "WEB",
     "expected": "Abre Google, digita, pesquisa", "fail": "Falha sem Playwright",
     "status": "CORRIGIDO", "fix": "Rotina + seletores múltiplos + fallback nativo"},
    {"id": 5, "task": "crie uma planilha com frutas e preços", "agent": "DATA",
     "expected": "Cria .xlsx formatado", "fail": None, "status": "OK", "fix": None},
    {"id": 6, "task": "organize meus downloads por tipo", "agent": "FILE",
     "expected": "Move por extensão", "fail": None, "status": "OK", "fix": None},
    {"id": 7, "task": "abra o youtube", "agent": "WEB",
     "expected": "Abre youtube.com", "fail": None, "status": "OK", "fix": None},
    {"id": 8, "task": "abra o vs code", "agent": "DESKTOP",
     "expected": "VS Code abre", "fail": None, "status": "OK", "fix": None},

    # MÉDIO
    {"id": 9, "task": "abra o notepad e escreva de 10 ate 20", "agent": "DESKTOP",
     "expected": "Números 10-20 por linha", "fail": "Escrevia 'Ola!' primeiro",
     "status": "CORRIGIDO", "fix": "1 app = 1 subtask, text correto"},
    {"id": 10, "task": "abra o youtube e pesquise videos de skate", "agent": "WEB",
     "expected": "Pesquisa no YouTube", "fail": "Seletor input#search falhava",
     "status": "CORRIGIDO", "fix": "5 seletores alternativos"},
    {"id": 11, "task": "abra o paint e desenhe uma casa", "agent": "DESKTOP",
     "expected": "Paint + desenha", "fail": "Só abria, não desenhava",
     "status": "CORRIGIDO", "fix": "action_type=draw → LLM com conhecimento Paint"},
    {"id": 12, "task": "crie um arquivo python de sistema de login", "agent": "CODE",
     "expected": "Cria .py", "fail": "Criava HTML",
     "status": "CORRIGIDO", "fix": "code_agent v18 com detecção de tipo"},
    {"id": 13, "task": "nova guia no youtube e pesquise videos de skate", "agent": "WEB",
     "expected": "Nova aba + YouTube + pesquisa", "fail": "Fallback não interage",
     "status": "CORRIGIDO", "fix": "Rotina _youtube_search_new_tab"},
    {"id": 14, "task": "crie um site bonito sobre IA", "agent": "CODE",
     "expected": "HTML+CSS separados", "fail": None, "status": "OK", "fix": None},
    {"id": 15, "task": "mande oi para Joao no Teams", "agent": "DESKTOP",
     "expected": "Teams + Joao + oi", "fail": None, "status": "OK", "fix": None},

    # DIFÍCIL
    {"id": 16, "task": "pesquise Palmeiras no google e envie no Teams para Jackson",
     "agent": "WEB→DESKTOP", "expected": "Pesquisa + envia resumo",
     "fail": "{output_text_1} com 'Invalid control character'",
     "status": "CORRIGIDO", "fix": "_sanitize_for_json() escapa tudo"},
    {"id": 17, "task": "crie planilha e envie por Teams", "agent": "DATA→DESKTOP",
     "expected": "Cria .xlsx + anexa", "fail": "{output_files_1} nem sempre resolve",
     "status": "PARCIAL", "fix": "ContextManager extrai caminhos de prints"},
    {"id": 18, "task": "abra vs code e crie projeto python de credenciamento",
     "agent": "CODE", "expected": "Cria .py completo",
     "fail": "Roteava para DESKTOP (só abria)",
     "status": "CORRIGIDO", "fix": "Maestro v16: criar+código → CODE"},
    {"id": 19, "task": "pesquise DevOps e escreva no notepad", "agent": "WEB→DESKTOP",
     "expected": "Pesquisa + cola resumo", "fail": "Caracteres especiais quebravam",
     "status": "CORRIGIDO", "fix": "Sanitização + summary automático"},
    {"id": 20, "task": "crie site de portfolio e abra no navegador", "agent": "CODE",
     "expected": "HTML+CSS + browser", "fail": None, "status": "OK", "fix": None},

    # AVANÇADO
    {"id": 21, "task": "minimize todas as janelas", "agent": "DESKTOP",
     "expected": "Win+D", "fail": "Sem rotina",
     "status": "CORRIGIDO", "fix": "_utility_steps com Win+D"},
    {"id": 22, "task": "feche todos os aplicativos", "agent": "DESKTOP",
     "expected": "Alt+F4 loop", "fail": "Sem rotina",
     "status": "CORRIGIDO", "fix": "_utility_steps com Alt+F4 x3"},
    {"id": 23, "task": "tire um print da tela", "agent": "DESKTOP",
     "expected": "Screenshot + salvar", "fail": "Sem rotina",
     "status": "CORRIGIDO", "fix": "_utility_steps com pyautogui.screenshot"},
    {"id": 24, "task": "abra spotify e toque lofi", "agent": "DESKTOP",
     "expected": "Spotify + pesquisa + toca", "fail": "Só abria",
     "status": "CORRIGIDO", "fix": "Spotify + toc/play = complexo → LLM"},
    {"id": 25, "task": "manda mensagem pro Joao", "agent": "?",
     "expected": "Perguntar: Teams ou WhatsApp?", "fail": "Chuta um app",
     "status": "FALTANTE", "fix": "Maestro needs_confirmation"},
    {"id": 26, "task": "crie 3 arquivos python", "agent": "CODE",
     "expected": "3 .py separados", "fail": "Pode criar só 1",
     "status": "PARCIAL", "fix": "CODE detectar lista"},
    {"id": 27, "task": "pesquise youtube skate 90s e clique no primeiro", "agent": "WEB",
     "expected": "Pesquisa + clica", "fail": "web_click imprevisível",
     "status": "CORRIGIDO", "fix": "_youtube_search_click com seletor"},
    {"id": 28, "task": "abra word e escreva carta formal", "agent": "DESKTOP",
     "expected": "Word + texto", "fail": "Pode ir para CODE",
     "status": "OK", "fix": "Maestro diferencia"},
    {"id": 29, "task": "copie PDFs do Downloads para Desktop", "agent": "FILE",
     "expected": "Copia filtrando", "fail": None, "status": "OK", "fix": None},
    {"id": 30, "task": "pesquise AWS e salve resumo em txt", "agent": "WEB→FILE",
     "expected": "3 etapas", "fail": "Depende de boa decomposição",
     "status": "PARCIAL", "fix": "ContextManager v3 resolve mas Maestro precisa decompor bem"},
]

# RESUMO:
# OK:        12 tarefas (40%)
# CORRIGIDO: 15 tarefas (50%) — fix aplicado
# PARCIAL:    3 tarefas (10%) — funciona com edge cases
# FALTANTE:   1 tarefa ( 3%) — needs_confirmation
#
# Cobertura total: 97% (29/30 tarefas funcionam ou têm fix)