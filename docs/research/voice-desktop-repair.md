# Diagnóstico de execução e voz — 2026-11-03

O erro reportado reproduziu confirmação dependente apenas do primeiro plano. A descoberta
agora identifica janelas de aplicativos conhecidos pelo processo, aceita uma janela de fundo
única e não escolhe um documento arbitrário quando existem vários alvos.

O modo Conversa classificava a saudação como feedback silencioso. Agora solicita resposta
falada. Erros do provedor também geram aviso na conversa, além de fallback local.

O log ModuleNotFoundError indica ambiente incompatível; main.py agora reutiliza o .venv
preparado quando iniciado por um Python global. iniciar.cmd oferece entrada explícita.
Diagnóstico de dependência informa o módulo ausente, sem expor credenciais.

Validação local: 80 testes aprovados, smoke existente, QML e integridade do vault aprovados.
Uma janela nativa real do Notepad foi aberta e identificada pelo novo resolvedor.

O teste real GPT-Live não concluiu: conexão encerrada antes de session.started/uso final.
Consulta HTTP ao catálogo do modelo retornou 200; handshake WebSocket de diagnóstico retornou
403 Forbidden. Catálogo disponível não comprova permissão para criar sessões. Não foi possível
estabelecer se o bloqueio vem da rede/proxy ou do acesso ao endpoint nesta conta.

A reserva antiga de 33 segundos foi preservada como consumo não confirmado, com backup do
contador, durante a recuperação operacional. Nenhum valor foi reembolsado/apagado. A tentativa
real posterior também ficou sem confirmação final; sua reserva permanece pendente. Não liberar
retries automáticos nem afirmar custo zero para uma sessão sem confirmação.

Conversação GPT-Live ponta a ponta e áudio humano permanecem sem validação. Corrigir o acesso
WebSocket e reconciliar o uso pendente antes de repetir teste pago. Reiniciar pelo iniciar.cmd
é necessário para carregar as correções no processo que já estava aberto.

## Causa do GPT-Live indisponível — atualização

Resolvido. O 403 não se repetiu: o handshake retorna 101. Todas as sessões eram recusadas porque o
app enviava `session.delegation: null`; a API responde `invalid_type` e fecha a conexão, e o código
descartava a mensagem. A reserva pendente fazia as tentativas seguintes falharem com `ValueError`.
Com `{"type": "client"}`, a sessão inicia e fala. Ver [voice-on-demand](../architecture/voice-on-demand.md).

## Ponte de respostas — atualização

A espera pela resposta agora é armada antes de despachar a tarefa. O evento de término não
rearma uma resposta já entregue. Publicações dos agentes incluem execução e sessão; a voz
recusa resultados atrasados de outra execução/conversa. No modo Conversa, resultados finais
também são falados quando o classificador antigo os considerava pouco informativos.
Isso mantém o Maestro/executor como fronteira de autorização, sem dar ferramentas ao narrador.

A validação completa passou após esta correção, incluindo cenários de resposta antes/depois
do término e mensagens de outra sessão. O SDK OpenAI disponível no ambiente de teste não
expunha a API Live; a instalação experimental foi removida, sem introduzir dependências ociosas.

A segunda reserva pendente foi recuperada conservadoramente por solicitação de reparo:
66 segundos continuam contabilizados como gastos, sem reembolso, com cópias anteriores e
registro das sessões não confirmadas. Pendência local liberada para uso pelo operador; isso
não comprova encerramento/faturamento do provedor e não remove o 403 observado nos testes.

Diagnóstico executável na própria máquina: `scripts/check_live_access.py`. Não envia
session.start nem microfone, não mostra a chave ou os headers e reporta apenas metadados
de conexão. Um handshake 101 ainda não certifica geração/fala; 403 requer investigar
permissão do projeto e rede/proxy. Não alterar endpoints/credenciais para contornar autorização.
