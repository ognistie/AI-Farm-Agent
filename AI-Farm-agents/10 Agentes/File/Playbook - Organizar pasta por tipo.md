---
tipo: playbook
agente: FILE
estado: curado
verificado: nao
keywords: organizar pasta downloads tipo extensao
revisado_em: 2026-10-31
tags: [playbook, file]
---
# Organizar pasta por tipo

Agente: [[File Agent]]

## Caminho
list_files na raiz autorizada -> inventario -> create_folder -> move_file por arquivo -> relatar sucessos e falhas.

## Limites e aceite
Nao operar fora do pedido nem sobrescrever destinos. Classificar por extensao nao implica entrar em subpastas. Em colisao, preservar e informar; nao prometer sufixo automatico.
