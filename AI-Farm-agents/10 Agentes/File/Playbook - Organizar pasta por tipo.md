---
tipo: playbook
agente: FILE
keywords: organizar pasta downloads tipo extensao
tags: [playbook, file]
cssclasses: [agent-file]
---
# Organizar pasta por tipo

Agente: [[File Agent]]

## Exemplo de pedido
> Organize os arquivos da pasta Downloads por tipo

## Caminho
1. Categorias: Imagens, Documentos, Planilhas, Vídeos, Áudio, Compactados, Código, Executáveis
2. Mover (shutil.move) com renome em conflito
3. Resumo por categoria

## Armadilhas
- Não mexer em subpastas existentes sem pedido.
