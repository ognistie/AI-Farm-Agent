// Tela principal. Sem tarefa: saudacao + caixa de entrada + sugestoes.
// Com tarefa: o pedido, o plano do Maestro, os passos em tempo real e o
// resultado (com links para o que foi criado e o custo real).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Item {
    id: root

    // idle | running | done | failed | cancelled | clarify
    property string status: "idle"
    property string task: ""
    property string phaseMsg: ""
    property string errorMsg: ""
    property string question: ""
    property string resolvedText: ""   // como o pedido foi entendido no contexto da conversa
    property string heardText: ""      // o que o microfone ouviu (se diferente do pedido)
    property string assistantText: ""  // resposta do assistente a este pedido (como numa conversa)
    readonly property bool hasConversation: turnsModel.count > 0
    property string reportSummary: ""
    property bool wasDryRun: false
    property real progress: 0
    property int elapsedMs: 0
    property double startedAt: 0

    // Uso de API: o Bridge manda o acumulado da sessao; guardamos a base
    // no inicio da tarefa para mostrar so o desta execucao.
    property var usageNow: ({ calls: 0, tokens_est: 0, cost_usd: 0 })
    property var usageBase: ({ calls: 0, tokens_est: 0, cost_usd: 0 })
    property var finalMetrics: null
    property var artifacts: ({ folder: "", files: [], url: "" })

    readonly property bool idle: status === "idle"
    readonly property bool running: status === "running"

    ListModel { id: turnsModel }  // pedidos anteriores da conversa { said, resolved, status, summary }
    ListModel { id: planModel }
    ListModel { id: replyModel }  // falas do agente (modo voz) neste pedido
    ListModel { id: stepModel }   // { n, agent, desc, state, result, kind }

    // ── API usada pelo Main ──────────────────────────────────────────
    // Nova conversa: esquece o contexto (o que foi feito e o que ficou aberto)
    function newTask() {
        if (running) return
        turnsModel.clear()
        Bridge.newSession()
        status = "idle"
        composer.text = ""
        composer.focusInput()
    }

    // Conversa salva reaberta pela barra lateral: pedidos e respostas voltam para a tela
    function showConversation(data) {
        if (running) return
        turnsModel.clear()
        for (const t of (data.turns || [])) {
            turnsModel.append({
                said: t.said || "", resolved: t.resolved || "",
                status: t.kind === "chat" ? "done" : (t.success === false ? "failed" : "done"),
                summary: (t.reply || t.summary || "").substring(0, 400)
            })
        }
        clearCurrent()
        composer.focusInput()
        scrollSoon()
    }

    // Pedido atual vira historico e a tela fica pronta para o proximo
    function clearCurrent() {
        status = "idle"; task = ""; resolvedText = ""; heardText = ""; assistantText = ""
        errorMsg = ""; question = ""; reportSummary = ""
        planModel.clear(); stepModel.clear(); replyModel.clear()
    }

    // Papo por voz ("valeu", "oi"): mensagem propria, sem grudar no pedido anterior
    function addChat(heard, reply) {
        if (running) { replyModel.append({ text: reply }); return }
        archiveTurn()
        clearCurrent()
        turnsModel.append({ said: heard, resolved: "", status: "done", summary: reply })
        scrollSoon()
    }

    function prefill(text) {
        if (running) return
        composer.text = text
        composer.focusInput()
    }

    // O pedido que terminou vai para o topo da conversa, em forma compacta
    function archiveTurn() {
        if (idle || !task) return
        const lastReply = replyModel.count ? replyModel.get(replyModel.count - 1).text : ""
        turnsModel.append({
            said: task, resolved: resolvedText, status: status,
            summary: (assistantText || reportSummary || errorMsg || question || lastReply || "").substring(0, 400)
        })
    }

    // heard: o que o microfone ouviu, quando o pedido veio por voz
    function start(text, heard) {
        archiveTurn()
        resolvedText = ""
        heardText = (heard && heard.trim().toLowerCase().replace(/[.!?,]/g, "")
                     !== text.trim().toLowerCase().replace(/[.!?,]/g, "")) ? heard : ""
        replyModel.clear()
        assistantText = ""
        task = text
        phaseMsg = "Entendendo o pedido"
        errorMsg = ""; question = ""; reportSummary = ""
        progress = 0
        elapsedMs = 0
        startedAt = Date.now()
        wasDryRun = composer.dryRun
        usageBase = usageNow
        finalMetrics = null
        artifacts = { folder: "", files: [], url: "" }
        planModel.clear()
        stepModel.clear()
        status = "running"
        composer.text = ""
        Bridge.executeTask(text, composer.dryRun, composer.genReport)
    }

    // ── Formatacao ───────────────────────────────────────────────────
    function fmtDuration(ms) {
        const s = Math.round(ms / 1000)
        return s < 60 ? s + "s" : Math.floor(s / 60) + "min " + (s % 60) + "s"
    }
    function fmtTokens(n) {
        return n >= 1000 ? (n / 1000).toFixed(1).replace(".", ",") + "k" : "" + n
    }
    function fmtCost(v) { return "US$ " + (v || 0).toFixed(4).replace(".", ",") }

    function usageLine() {
        const m = finalMetrics
        const calls = m ? m.api_calls : usageNow.calls - usageBase.calls
        const tokens = m ? m.tokens_est : usageNow.tokens_est - usageBase.tokens_est
        const cost = m ? m.cost_usd : usageNow.cost_usd - usageBase.cost_usd
        const parts = [fmtDuration(elapsedMs)]
        if (calls > 0) parts.push(calls + (calls === 1 ? " chamada" : " chamadas"),
                                  fmtTokens(tokens) + " tokens", fmtCost(cost))
        return parts.join("  ·  ")
    }

    function parseAgent(desc) {
        const m = (desc || "").match(/^\[(\w+)\]\s*/)
        return m ? { agent: m[1], text: desc.substring(m[0].length) } : { agent: "", text: desc || "" }
    }

    function findStep(n) {
        for (let i = 0; i < stepModel.count; i++)
            if (stepModel.get(i).kind === "step" && stepModel.get(i).n === n) return i
        return -1
    }

    function scrollSoon() { scrollTimer.restart() }

    Timer { id: scrollTimer; interval: 30; onTriggered: transcript.scrollToEnd() }

    Timer {
        interval: 250; repeat: true; running: root.running
        onTriggered: root.elapsedMs = Date.now() - root.startedAt
    }

    // ── Eventos do backend ──────────────────────────────────────────
    Connections {
        target: Bridge

        function onPhaseChanged(json) {
            const p = JSON.parse(json)
            if (p.msg) root.phaseMsg = p.msg
        }
        function onPlanReady(json) {
            const plan = JSON.parse(json).plan || {}
            planModel.clear()
            for (const s of (plan.steps || [])) {
                const a = root.parseAgent(s.description)
                planModel.append({ agent: a.agent || s.action || "", text: a.text })
            }
            root.phaseMsg = "Executando"
            root.scrollSoon()
        }
        function onStepStart(json) {
            const s = JSON.parse(json)
            const a = root.parseAgent(s.desc)
            stepModel.append({ kind: "step", n: s.step, agent: a.agent, desc: a.text,
                               state: "running", result: "" })
            root.progress = s.progress || root.progress
            root.phaseMsg = "Passo " + s.step + (s.total ? " de " + s.total : "")
            root.scrollSoon()
        }
        function onStepDone(json) {
            const s = JSON.parse(json)
            const i = root.findStep(s.step)
            const result = (s.result || "").toString().trim().substring(0, 600)
            if (i >= 0) {
                stepModel.setProperty(i, "state", s.ok ? "ok" : "fail")
                stepModel.setProperty(i, "result", result)
            } else {
                const a = root.parseAgent(s.desc)
                stepModel.append({ kind: "step", n: s.step, agent: a.agent, desc: a.text,
                                   state: s.ok ? "ok" : "fail", result: result })
            }
            root.progress = s.progress || root.progress
        }
        function onLogEntry(json) {
            // So o que o usuario precisa saber: avisos e erros que nao
            // viraram passo (ex.: "Plano falhou" de um agente).
            const e = JSON.parse(json)
            const level = (e.level || "").toUpperCase()
            const msg = e.msg || ""
            if (!root.running) return
            if (level !== "ERROR" && level !== "WARN") return
            if (msg.indexOf("Step falhou") === 0) return
            stepModel.append({ kind: "note", n: -1, agent: e.agent || "",
                               desc: msg, state: level === "ERROR" ? "fail" : "warn", result: "" })
            root.scrollSoon()
        }
        function onApiUsage(json) { root.usageNow = JSON.parse(json) }
        function onContextExtracted(json) {
            const c = JSON.parse(json)
            root.artifacts = {
                folder: c.folder || root.artifacts.folder,
                files: (c.files && c.files.length) ? c.files : root.artifacts.files,
                url: c.url || root.artifacts.url
            }
        }
        function onTaskDone(json) {
            root.progress = 100
            root.phaseMsg = "Finalizando"
        }
        function onReportReady(json) {
            const r = JSON.parse(json).report || {}
            root.reportSummary = r.summary || ""
        }
        function onCancelled(json) {
            if (root.status === "running") root.status = "cancelled"
        }
        function onErrorRaised(json) {
            const e = JSON.parse(json)
            if (e.kind === "clarification") {
                root.question = e.msg || "Pode dar mais detalhes?"
                root.status = "clarify"
                composer.text = ""
                composer.focusInput()
            } else if (e.kind === "limitation") {
                // O Maestro decidiu nao cumprir como pedido (ex.: obra protegida)
                root.question = e.msg || "Nao posso fazer isso como pedido."
                root.status = "limited"
                composer.focusInput()
            } else {
                root.errorMsg = e.msg || "Erro desconhecido"
                root.status = "failed"
            }
            root.scrollSoon()
        }
        function onResolved(json) {
            const r = JSON.parse(json)
            if (r.said === root.task && r.task !== r.said) root.resolvedText = r.task
        }
        function onVoiceState(json) {
            const v = JSON.parse(json)
            if (v.state === "recording" && composer.voiceState !== "recording")
                composer.recStartedAt = Date.now()
            composer.voiceState = v.state || "idle"
            composer.liveOn = !!v.live
            composer.queued = v.queued || 0
            if (v.hotkey) composer.voiceHotkey = v.hotkey.split("+").map(k =>
                k === "space" ? "Espaço" : k.charAt(0).toUpperCase() + k.slice(1)).join("+")
        }
        function onVoiceLevel(json) { composer.voiceLevel = JSON.parse(json).level || 0 }
        function onVoiceReply(json) {
            // O que o agente falou em voz alta aparece na conversa
            const t = JSON.parse(json).text || ""
            if (t && !root.idle) { replyModel.append({ text: t }); root.scrollSoon() }
        }
        function onAssistantMessage(json) {
            const m = JSON.parse(json)
            if (m.said === root.task) { root.assistantText = m.text || ""; root.scrollSoon() }
        }
        function onVoiceChat(json) {
            const c = JSON.parse(json)
            root.addChat(c.heard || "", c.reply || "")
        }
        function onAnswerReady(json) {
            // Pergunta sobre algo ja feito: respondida pela conversa, sem acao
            root.reportSummary = JSON.parse(json).msg || ""
        }
        function onHistoryChanged(json) {
            // Registro final: sucesso real, metricas desta execucao, artefatos.
            const entry = JSON.parse(json).entry || {}
            if (entry.task !== root.task) return
            root.finalMetrics = entry.metrics || null
            root.elapsedMs = entry.duration_ms || root.elapsedMs
            const art = entry.artifacts || {}
            root.artifacts = {
                folder: art.folder || root.artifacts.folder,
                files: (art.files && art.files.length) ? art.files : root.artifacts.files,
                url: art.url || root.artifacts.url
            }
            if (root.status === "running")
                root.status = entry.success ? "done" : "failed"
            if (root.status === "failed" && !root.errorMsg)
                root.errorMsg = entry.error || "Um ou mais passos não funcionaram."
            root.scrollSoon()
        }
    }

    // ══ Estado inicial: saudacao ════════════════════════════════════
    ColumnLayout {
        id: hero
        visible: root.idle && !root.hasConversation
        width: composer.width
        x: composer.x
        y: Math.max(C.Theme.sp6, composer.y - implicitHeight - 28)
        spacing: 8

        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: "O que você quer que eu faça?"
            color: C.Theme.textPrimary
            font.family: C.Theme.fontDisplay
            font.pixelSize: C.Theme.sizeHero
            font.weight: Font.DemiBold
            wrapMode: Text.Wrap
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: "Descreva em linguagem natural. O Maestro escolhe o agente certo e executa no seu computador."
            color: C.Theme.textSecondary
            font.family: C.Theme.fontSans
            font.pixelSize: C.Theme.sizeMd
            wrapMode: Text.Wrap
        }
    }

    Flow {
        id: suggestions
        visible: root.idle && !root.hasConversation
        x: composer.x
        width: composer.width
        y: composer.y + composer.height + 16
        spacing: 8

        Repeater {
            model: [
                { i: "", t: "Crie uma planilha de gastos do mês com gráfico" },
                { i: "", t: "Pesquise no Google sobre inteligência artificial" },
                { i: "", t: "Crie um site sobre uma cafeteria artesanal" },
                { i: "", t: "Organize os arquivos da pasta Downloads por tipo" },
            ]
            delegate: Rectangle {
                width: sugRow.implicitWidth + 24
                height: 34
                radius: 17
                color: sugMouse.containsMouse ? C.Theme.bgHover : "transparent"
                border.width: 1
                border.color: C.Theme.hairline
                RowLayout {
                    id: sugRow
                    anchors.centerIn: parent
                    spacing: 8
                    C.Icon { glyph: modelData.i; size: 13 }
                    Text {
                        text: modelData.t
                        color: C.Theme.textSecondary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeSm + 1
                    }
                }
                MouseArea {
                    id: sugMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.prefill(modelData.t)
                }
            }
        }
    }

    // ══ Execucao: transcricao ═══════════════════════════════════════
    C.ScrollPage {
        id: transcript
        visible: !root.idle || root.hasConversation
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: composer.top
        anchors.bottomMargin: 8
        topPadding: 40
        bottomPadding: 16
        spacing: 20

        // Pedidos anteriores da conversa (compactos)
        Repeater {
            model: turnsModel
            delegate: PastTurn {
                Layout.fillWidth: true
                said: model.said
                status: model.status
                summary: model.summary
            }
        }

        // Pedido do usuario
        Rectangle {
            visible: !root.idle
            Layout.alignment: Qt.AlignRight
            Layout.maximumWidth: parent.width * 0.8
            implicitWidth: Math.min(taskText.implicitWidth + 32, parent.width * 0.8)
            implicitHeight: taskText.implicitHeight + 20
            radius: 18
            color: C.Theme.bgSurfaceHi
            Text {
                id: taskText
                anchors.fill: parent
                anchors.leftMargin: 16; anchors.rightMargin: 16
                anchors.topMargin: 10; anchors.bottomMargin: 10
                text: root.task
                color: C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd + 1
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
            }
        }

        // O que o microfone ouviu (pedido por voz)
        Text {
            visible: root.heardText !== ""
            Layout.alignment: Qt.AlignRight
            Layout.maximumWidth: parent.width * 0.8
            Layout.topMargin: -12
            text: "Ouvi: “" + root.heardText + "”"
            color: C.Theme.textTertiary
            font.family: C.Theme.fontSans
            font.pixelSize: C.Theme.sizeSm
            font.italic: true
            wrapMode: Text.Wrap
            horizontalAlignment: Text.AlignRight
        }

        // Falas do agente (modo voz)
        Repeater {
            model: replyModel
            delegate: RowLayout {
                Layout.fillWidth: true
                spacing: 8
                C.Icon { glyph: ""; size: 12; color: C.Theme.textTertiary; Layout.alignment: Qt.AlignTop; Layout.topMargin: 2 }
                Text {
                    Layout.fillWidth: true
                    text: model.text
                    color: C.Theme.textSecondary
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeMd
                    wrapMode: Text.Wrap
                }
            }
        }

        // Como o pedido foi entendido (continuacao da conversa)
        Text {
            visible: root.resolvedText !== ""
            Layout.alignment: Qt.AlignRight
            Layout.maximumWidth: parent.width * 0.8
            Layout.topMargin: -12
            text: "Entendi: " + root.resolvedText
            color: C.Theme.textTertiary
            font.family: C.Theme.fontSans
            font.pixelSize: C.Theme.sizeSm
            wrapMode: Text.Wrap
            horizontalAlignment: Text.AlignRight
        }

        // Status da execucao
        ColumnLayout {
            visible: !root.idle
            Layout.fillWidth: true
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                C.Spinner { visible: root.running; size: 14 }
                C.Icon {
                    visible: !root.running
                    size: 14
                    glyph: root.status === "done" ? ""
                         : (root.status === "clarify" || root.status === "limited") ? ""
                         : root.status === "cancelled" ? "" : ""
                    color: root.status === "done" ? C.Theme.success
                         : (root.status === "clarify" || root.status === "limited") ? C.Theme.info
                         : root.status === "cancelled" ? C.Theme.textSecondary : C.Theme.danger
                }
                Text {
                    Layout.fillWidth: true
                    text: {
                        switch (root.status) {
                            case "running":   return root.phaseMsg + "..."
                            case "done":      return root.wasDryRun ? "Simulação concluída — nada foi executado"
                                                                    : "Tarefa concluída"
                            case "failed":    return "Não foi possível concluir"
                            case "cancelled": return "Execução interrompida"
                            case "clarify":   return "Preciso de mais detalhes"
                            case "limited":   return "Não vou fazer isso como foi pedido"
                        }
                        return ""
                    }
                    color: C.Theme.textPrimary
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeMd
                    font.weight: Font.Medium
                    elide: Text.ElideRight
                }
                Text {
                    text: root.usageLine()
                    color: C.Theme.textTertiary
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeSm
                }
            }

            // Barra de progresso fina
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 2
                visible: root.running
                radius: 1
                color: C.Theme.hairline
                Rectangle {
                    width: parent.width * Math.max(0.03, Math.min(1, root.progress / 100))
                    height: parent.height
                    radius: 1
                    color: C.Theme.textPrimary
                    Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                }
            }
        }

        // Pergunta do Maestro (ambiguidade)
        Rectangle {
            visible: root.status === "clarify" || root.status === "limited"
            Layout.fillWidth: true
            implicitHeight: qText.implicitHeight + 28
            radius: C.Theme.rMd
            color: C.Theme.alpha(C.Theme.info, 0.08)
            border.width: 1
            border.color: C.Theme.alpha(C.Theme.info, 0.25)
            Text {
                id: qText
                anchors.fill: parent
                anchors.margins: 14
                text: root.question + (root.status === "clarify"
                      ? "\n\nResponda abaixo — eu continuo o mesmo pedido."
                      : "\n\nVocê pode reformular o pedido abaixo.")
                color: C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
                wrapMode: Text.Wrap
            }
        }

        // Plano
        ColumnLayout {
            visible: planModel.count > 0
            Layout.fillWidth: true
            spacing: 6

            Text {
                text: "Plano"
                color: C.Theme.textTertiary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeSm
                font.weight: Font.Medium
            }
            Repeater {
                model: planModel
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Text {
                        text: (index + 1) + "."
                        color: C.Theme.textTertiary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeMd
                        Layout.preferredWidth: 18
                        Layout.alignment: Qt.AlignTop
                    }
                    Text {
                        Layout.fillWidth: true
                        text: model.text
                        color: C.Theme.textSecondary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeMd
                        wrapMode: Text.Wrap
                    }
                    AgentTag { agent: model.agent; Layout.alignment: Qt.AlignTop }
                }
            }
        }

        // Passos
        ColumnLayout {
            visible: stepModel.count > 0
            Layout.fillWidth: true
            spacing: 2

            Text {
                text: "Passos"
                color: C.Theme.textTertiary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeSm
                font.weight: Font.Medium
                Layout.bottomMargin: 4
            }
            Repeater {
                model: stepModel
                delegate: StepRow {
                    Layout.fillWidth: true
                    desc: model.desc
                    agent: model.agent
                    status: model.state
                    result: model.result
                    kind: model.kind
                }
            }
        }

        // Resultado
        ColumnLayout {
            visible: !root.idle && !root.running && root.status !== "clarify"
            Layout.fillWidth: true
            spacing: 12

            Text {
                visible: root.status === "failed" && root.errorMsg !== ""
                Layout.fillWidth: true
                text: root.errorMsg
                color: C.Theme.textSecondary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
                wrapMode: Text.Wrap
                maximumLineCount: 6
                elide: Text.ElideRight
            }

            Text {
                visible: root.assistantText !== ""
                Layout.fillWidth: true
                text: root.assistantText
                color: C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd + 1
                lineHeight: 1.3
                wrapMode: Text.Wrap
            }

            Text {
                visible: root.reportSummary !== ""
                Layout.fillWidth: true
                text: root.reportSummary
                color: C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
                lineHeight: 1.3
                wrapMode: Text.Wrap
            }

            Flow {
                Layout.fillWidth: true
                spacing: 8
                C.Button {
                    visible: !!root.artifacts.folder
                    text: "Abrir pasta"
                    icon: ""
                    compact: true
                    onClicked: Qt.openUrlExternally("file:///" + root.artifacts.folder)
                }
                C.Button {
                    visible: !!root.artifacts.url
                    text: "Abrir link"
                    icon: ""
                    compact: true
                    onClicked: Qt.openUrlExternally(root.artifacts.url)
                }
                C.Button {
                    visible: root.status === "failed" || root.status === "cancelled"
                    text: "Tentar de novo"
                    icon: ""
                    compact: true
                    onClicked: root.start(root.task)
                }
                C.Button {
                    text: "Nova conversa"
                    icon: ""
                    variant: "ghost"
                    compact: true
                    onClicked: root.newTask()
                }
            }
        }
    }

    // ══ Caixa de entrada (centro no inicio, rodape durante a execucao) ══
    C.Composer {
        id: composer
        width: Math.min(C.Theme.contentMax, root.width - 48)
        x: (root.width - width) / 2
        y: (root.idle && !root.hasConversation) ? Math.round(root.height * 0.42) : root.height - height - 20
        running: root.running
        placeholder: (root.idle && !root.hasConversation) ? "Ex.: crie uma planilha de vendas do trimestre e abra no Excel"
                   : root.running ? "Executando... pressione Esc para parar"
                   : "Continue a conversa (ex.: agora abra o segundo vídeo)..."
        onSubmitted: (t) => root.start(t)
        onStopRequested: Bridge.forceStop()
        onMicClicked: Bridge.voiceRecordToggle()
        onRecordCancel: Bridge.voiceRecordCancel()
        onLiveSwitched: (on) => Bridge.setLiveConversation(on)
        Behavior on y { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
        Component.onCompleted: focusInput()
    }

    // ── Subcomponentes locais ────────────────────────────────────────
    component AgentTag: Text {
        property string agent: ""
        visible: agent !== ""
        text: C.Theme.agentLabel(agent)
        color: C.Theme.textTertiary
        font.family: C.Theme.fontSans
        font.pixelSize: C.Theme.sizeSm
    }

    // Pedido anterior da conversa: o que foi dito + resultado em uma linha
    component PastTurn: ColumnLayout {
        id: past
        property string said: ""
        property string status: ""
        property string summary: ""
        spacing: 6
        opacity: 0.8

        Rectangle {
            Layout.alignment: Qt.AlignRight
            Layout.maximumWidth: past.width * 0.8
            implicitWidth: Math.min(pastSaid.implicitWidth + 28, past.width * 0.8)
            implicitHeight: pastSaid.implicitHeight + 16
            radius: 16
            color: C.Theme.bgSurfaceHi
            Text {
                id: pastSaid
                anchors.fill: parent
                anchors.leftMargin: 14; anchors.rightMargin: 14
                anchors.topMargin: 8; anchors.bottomMargin: 8
                text: past.said
                color: C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            C.Icon {
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 2
                size: 12
                glyph: past.status === "done" ? ""
                     : (past.status === "clarify" || past.status === "limited") ? ""
                     : past.status === "cancelled" ? "" : ""
                color: past.status === "done" ? C.Theme.success
                     : (past.status === "clarify" || past.status === "limited") ? C.Theme.info
                     : past.status === "cancelled" ? C.Theme.textSecondary : C.Theme.danger
            }
            Text {
                Layout.fillWidth: true
                text: past.summary !== "" ? past.summary
                      : past.status === "done" ? "Concluído"
                      : past.status === "cancelled" ? "Interrompido" : "Não concluído"
                color: C.Theme.textSecondary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeSm + 1
                wrapMode: Text.Wrap
                maximumLineCount: 3
                elide: Text.ElideRight
            }
        }
        Rectangle { Layout.fillWidth: true; Layout.topMargin: 6; implicitHeight: 1; color: C.Theme.hairline }
    }

    component StepRow: ColumnLayout {
        id: row
        property string desc: ""
        property string agent: ""
        property string status: "running"   // running | ok | fail | warn
        property string result: ""
        property string kind: "step"
        property bool expanded: false
        spacing: 2

        RowLayout {
            Layout.fillWidth: true
            Layout.minimumHeight: 30
            spacing: 10

            Item {
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                C.Spinner { anchors.centerIn: parent; visible: row.status === "running"; size: 13 }
                C.Icon {
                    anchors.centerIn: parent
                    visible: row.status !== "running"
                    size: 12
                    glyph: row.status === "ok" ? "" : row.status === "warn" ? "" : ""
                    color: row.status === "ok" ? C.Theme.success
                         : row.status === "warn" ? C.Theme.warning : C.Theme.danger
                }
            }
            Text {
                Layout.fillWidth: true
                text: row.desc
                color: row.kind === "note" ? C.Theme.textSecondary : C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
                elide: row.expanded ? Text.ElideNone : Text.ElideRight
                wrapMode: row.expanded ? Text.Wrap : Text.NoWrap
            }
            AgentTag { agent: row.agent }
            C.Icon {
                visible: row.result !== ""
                glyph: row.expanded ? "" : ""
                size: 10
                color: C.Theme.textTertiary
            }
        }

        Text {
            visible: row.expanded && row.result !== ""
            Layout.fillWidth: true
            Layout.leftMargin: 26
            Layout.bottomMargin: 6
            text: row.result
            color: C.Theme.textSecondary
            font.family: C.Theme.fontMono
            font.pixelSize: C.Theme.sizeXs + 1
            wrapMode: Text.WrapAnywhere
            textFormat: Text.PlainText
        }

        TapHandler {
            enabled: row.result !== ""
            onTapped: row.expanded = !row.expanded
        }
        HoverHandler { cursorShape: row.result !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor }
    }
}
