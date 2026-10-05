---
tipo: dicionario
tags: [dicionario, voz]
cssclasses: [agent-maestro]
atualizado: 2026-10-05
---

# 📖 Dicionário de voz (português do Brasil)

← [[Modo voz]] · [[Conversa continua]] · [[Persona do assistente]]

> [!lesson] Para que serve
> Como a gente **fala** e como o agente deve **agir**: gírias, apelidos de apps, jeitos de pedir, termos do computador, páginas das Configurações, atalhos, muletas e os erros comuns da transcrição. O agente corrige o que ouviu, entende a intenção e escolhe o caminho mais curto; na dúvida, **pergunta uma vez** em vez de adivinhar.

## Notas

| Nota | Linhas | Jeitos de falar | Quem usa |
|---|---|---|---|
| [[Apps e sites]] | 154 | 491 | voz (nomes), resolvedor (pedido novo × continuar), Desktop/Web (como abrir) |
| [[Formas de pedir]] | 71 | 371 | voz (intenção), agentes (como executar, quando confirmar) |
| [[Termos de computador]] | 117 | 376 | voz e todos os agentes (o que é e onde fica) |
| [[Configuracoes do Windows]] | 62 | 182 | Desktop (abre a página exata) |
| [[Atalhos de teclado]] | 81 | 144 | pilotos de apps e do navegador |
| [[Girias e expressoes]] | 137 | 484 | voz |
| [[Muletas e ruido]] | 28 | 93 | voz (o que descartar) |
| [[Confusoes de transcricao]] | 101 | 234 | voz (auto = corrige antes; dica = pista) |
| [[Numeros e tempo]] | 48 | 168 | voz e agentes (contas, datas) |
| [[Referencias e contexto]] | 23 | 87 | voz e resolvedor de conversa |

**Total:** 822 linhas, 2630 jeitos de falar.

## Como o agente usa
1. **Confusões** com `auto` corrigem o texto ouvido antes de tudo ("google escute" → VS Code); as `dica` vão só como pista.
2. As linhas que aparecem na fala vão para o entendimento de voz (as mais específicas primeiro).
3. Os agentes recebem as linhas de **Termos**, **Formas de pedir**, **Configurações**, **Atalhos** e **Apps** que tocam no pedido, junto com playbooks e [[Licoes aprendidas]] ([[Como usar o cerebro]]).
4. Se a fala cita um app/site diferente do que está aberto, é pedido **novo**.
5. Nada aqui amplia permissões: senha, pagamento, apagar e enviar continuam exigindo o usuário.

## Como ensinar
Edite qualquer tabela: 1ª coluna = jeitos de falar separados por ` / `; 2ª = o que significa. O agente relê o dicionário a cada pedido (sem reiniciar). Em **Confusões**, use `auto` só para o que nunca é dito de propósito.

## Medição
- [[Avaliacao de voz]] — falas difíceis (nomes mal ouvidos, gíria, ruído) e como o agente se saiu.
