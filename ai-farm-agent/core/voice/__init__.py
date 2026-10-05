"""Modo voz: gravar a fala, transcrever localmente e responder falando.

recorder  microfone -> trecho de fala (detecta inicio e fim pela energia)
stt       faster-whisper local (portugues), carregado sob demanda
tts       voz do Windows (SAPI, pt-BR) numa thread propria
hotkey    atalho global (RegisterHotKey) para falar sem focar a janela
"""
