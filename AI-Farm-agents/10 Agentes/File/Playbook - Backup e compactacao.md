---
tipo: playbook
agente: FILE
estado: planejado
verificado: nao
keywords: backup zip compactar copia
revisado_em: 2026-10-31
tags: [playbook, file]
---
# Backup e compactacao

Agente: [[File Agent]]

## Limites e aceite
ZIP e descompactacao ainda nao sao ferramentas permitidas do FILE. Oferecer copia delimitada via copy_file quando isso satisfizer o pedido e houver escopo; caso contrario informar a limitacao. Nao emitir shutil.make_archive, extractall ou shell.
