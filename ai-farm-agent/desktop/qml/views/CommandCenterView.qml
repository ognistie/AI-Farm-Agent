// Command Center — estetica Claude/Lanes.sh.
// Topo: hero + input grande clean. Meio: grade 2x3 de metricas.
// Inferior: dois cards iguais (Execution Plan | Log Feed) com vidro fume.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Item {
    id: root

    // ── Estado local ─────────────────────────────────────────────────
    property bool dryRun: false
    property bool genReport: true
    property bool running: false
    property real progress: 0
    property string phaseLabel: "aguardando comando"
    property string mode: "Balanced"

    ListModel { id: feedModel }
    ListModel { id: planModel }

    property int apiCalls: 0
    property string apiTokens: "0"
    property string apiCost: "$0.0000"
    property int tasksCount: 0
    property int activeAgents: 0

    // ── Listeners ────────────────────────────────────────────────────
    Connections {
        target: Bridge
        function onRunningChanged(r) { root.running = r; if (r) root.progress = 0 }
        function onPhaseChanged(json) {
            const p = JSON.parse(json)
            root.phaseLabel = (p.msg || p.phase || "").toString()
        }
        function onPlanReady(json) {
            const data = JSON.parse(json).plan
            planModel.clear()
            for (const s of (data.steps || [])) planModel.append(s)
        }
        function onStepStart(json) {
            const s = JSON.parse(json)
            feedModel.append({ kind: "start", desc: s.desc, action: s.action, ok: true, result: "" })
            root.progress = s.progress || 0
            root.activeAgents = 1
        }
        function onStepDone(json) {
            const s = JSON.parse(json)
            feedModel.append({
                kind: "done", desc: s.desc, action: s.action,
                ok: s.ok, result: (s.result || "").toString().substring(0, 700)
            })
            root.progress = s.progress || 0
        }
        function onApiUsage(json) {
            const u = JSON.parse(json)
            root.apiCalls = u.calls || 0
            root.apiTokens = (u.tokens_est >= 1000)
                ? (u.tokens_est / 1000).toFixed(1) + "k"
                : ("" + (u.tokens_est || 0))
            root.apiCost = "$" + (u.cost_usd || 0).toFixed(4)
        }
        function onTaskDone(json) {
            root.tasksCount += 1
            root.progress = 100
            root.activeAgents = 0
            feedModel.append({ kind: "end", desc: "Tarefa concluida.", action: "DONE", ok: true, result: "" })
        }
        function onCancelled(json) {
            root.activeAgents = 0
            feedModel.append({ kind: "cancel", desc: "Execucao interrompida.", action: "CANCEL", ok: false, result: "" })
        }
        function onErrorRaised(json) {
            const e = JSON.parse(json)
            root.activeAgents = 0
            feedModel.append({ kind: "error", desc: e.msg || "Erro desconhecido", action: "ERROR", ok: false, result: "" })
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true
        // Barras invisiveis — rolagem ainda funciona via mouse wheel / trackpad
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: root.width
            spacing: 28

            // ═══ HERO + INPUT ══════════════════════════════════════
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 36
                Layout.rightMargin: 36
                Layout.topMargin: 32
                spacing: 22

                // Hero
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text {
                        text: "Escreva uma tarefa para sua rede de agentes."
                        color: C.Theme.textPrimary
                        font.family: C.Theme.fontSans
                        font.pixelSize: 28
                        font.weight: Font.DemiBold
                        font.letterSpacing: -0.6
                    }
                    Text {
                        text: "O Maestro escolhe o especialista certo e coordena a execucao em tempo real."
                        color: C.Theme.textSecondary
                        font.family: C.Theme.fontSans
                        font.pixelSize: 13
                    }
                }

                // Campo de texto
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 132
                    color: Qt.rgba(0.071, 0.075, 0.086, 0.72)
                    radius: C.Theme.rLg
                    border.color: input.activeFocus
                        ? C.Theme.alpha(C.Theme.accent, 0.55)
                        : Qt.rgba(1, 1, 1, 0.06)
                    border.width: 1

                    Rectangle {
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.margins: 1
                        height: 1
                        radius: parent.radius
                        color: Qt.rgba(1, 1, 1, 0.04)
                    }

                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 18
                        clip: true
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        ScrollBar.vertical.policy: ScrollBar.AlwaysOff

                        TextArea {
                            id: input
                            placeholderText: "Descreva sua tarefa, como 'Crie um relatorio de vendas do Q1'..."
                            color: C.Theme.textPrimary
                            placeholderTextColor: C.Theme.textMuted
                            selectionColor: C.Theme.alpha(C.Theme.accent, 0.35)
                            background: null
                            font.family: C.Theme.fontSans
                            font.pixelSize: 15
                            wrapMode: TextArea.Wrap
                            topPadding: 0; bottomPadding: 0
                            leftPadding: 0; rightPadding: 0
                        }
                    }
                }

                // Botoes de modo + acoes
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    C.ActionButton { text: "Fast";          variant: "mode"; selected: root.mode === "Fast";          onClicked: root.mode = "Fast" }
                    C.ActionButton { text: "Balanced";      variant: "mode"; selected: root.mode === "Balanced";      onClicked: root.mode = "Balanced" }
                    C.ActionButton { text: "Deep Analysis"; variant: "mode"; selected: root.mode === "Deep Analysis"; onClicked: root.mode = "Deep Analysis" }

                    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 22; Layout.leftMargin: 8; Layout.rightMargin: 8; color: C.Theme.hairline }

                    C.ActionButton { text: "Simulate"; variant: "mode"; selected: root.dryRun;    onClicked: root.dryRun = !root.dryRun }
                    C.ActionButton { text: "Report";   variant: "mode"; selected: root.genReport; onClicked: root.genReport = !root.genReport }

                    Item { Layout.fillWidth: true }

                    C.ActionButton {
                        text: "Clear"
                        variant: "ghost"
                        enabled: !root.running
                        onClicked: {
                            input.text = ""
                            feedModel.clear()
                            planModel.clear()
                            root.progress = 0
                        }
                    }
                    C.ActionButton {
                        text: "Abort"
                        variant: "danger"
                        visible: root.running
                        onClicked: Bridge.forceStop()
                    }
                    C.ActionButton {
                        text: root.running ? "Executing..." : "Run Task"
                        trailing: root.running ? "" : "→"
                        variant: "primary"
                        enabled: !root.running && input.text.trim().length > 0
                        onClicked: Bridge.executeTask(input.text, root.dryRun, root.genReport)
                    }
                }
            }

            // ═══ GRADE 2x3 DE METRICAS ═════════════════════════════
            GridLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 36
                Layout.rightMargin: 36
                columns: root.width < 760 ? 2 : 3
                columnSpacing: 14
                rowSpacing: 14

                C.MetricCard {
                    Layout.fillWidth: true
                    value: root.apiCost
                    label: "Custo"
                    glyph: "$"
                    accentColor: C.Theme.accent
                }
                C.MetricCard {
                    Layout.fillWidth: true
                    value: "" + root.activeAgents
                    label: "Agentes Ativos"
                    glyph: "◇"
                    accentColor: C.Theme.violet
                }
                C.MetricCard {
                    Layout.fillWidth: true
                    value: Math.round(root.progress) + "%"
                    label: "Progresso"
                    glyph: "▸"
                    accentColor: C.Theme.accent
                }
                C.MetricCard {
                    Layout.fillWidth: true
                    value: "" + root.apiCalls
                    label: "API Calls"
                    glyph: "≡"
                    accentColor: C.Theme.info
                }
                C.MetricCard {
                    Layout.fillWidth: true
                    value: root.apiTokens
                    label: "Tokens"
                    glyph: "⌬"
                    accentColor: C.Theme.cyan
                }
                C.MetricCard {
                    Layout.fillWidth: true
                    value: "" + root.tasksCount
                    label: "Tarefas"
                    glyph: "▢"
                    accentColor: C.Theme.violet
                }
            }

            // ═══ DOIS PAINEIS — Execution Plan | Log Feed ══════════
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 36
                Layout.rightMargin: 36
                Layout.bottomMargin: 32
                Layout.preferredHeight: 340
                spacing: 14

                // ─── EXECUTION PLAN ──────────────────────────────
                C.Card {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    Layout.fillHeight: true
                    title: "Execution Plan"
                    subtitle: planModel.count > 0
                        ? (planModel.count + " subtarefa(s) distribuida(s)")
                        : "Aguardando plano"

                    // Estado vazio premium
                    ColumnLayout {
                        anchors.centerIn: parent
                        visible: planModel.count === 0
                        spacing: 10

                        // Icone de subtarefa minimalista
                        Item {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            Layout.alignment: Qt.AlignHCenter
                            Rectangle {
                                anchors.fill: parent
                                radius: 12
                                color: C.Theme.alpha(C.Theme.accent, 0.08)
                                border.color: C.Theme.alpha(C.Theme.accent, 0.18)
                                border.width: 1
                            }
                            Column {
                                anchors.centerIn: parent
                                spacing: 2
                                Repeater {
                                    model: 3
                                    delegate: Rectangle {
                                        width: 16; height: 2; radius: 1
                                        color: C.Theme.accent
                                        opacity: 1 - index * 0.30
                                    }
                                }
                            }
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Aguardando plano..."
                            color: C.Theme.textSecondary
                            font.family: C.Theme.fontSans
                            font.pixelSize: 13
                            font.weight: Font.Medium
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Subtarefas aparecerao aqui ao executar."
                            color: C.Theme.textMuted
                            font.family: C.Theme.fontSans
                            font.pixelSize: 12
                        }
                    }

                    // Lista de subtarefas
                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 16
                        anchors.topMargin: 6
                        visible: planModel.count > 0
                        clip: true
                        contentWidth: availableWidth
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        ScrollBar.vertical.policy: ScrollBar.AlwaysOff

                        ColumnLayout {
                            width: parent.width
                            spacing: 6

                            Repeater {
                                model: planModel
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: planItem.implicitHeight + 16
                                    radius: C.Theme.rSm
                                    color: Qt.rgba(1, 1, 1, 0.02)
                                    border.color: Qt.rgba(1, 1, 1, 0.05)
                                    border.width: 1

                                    RowLayout {
                                        id: planItem
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 12
                                        spacing: 10

                                        Rectangle {
                                            Layout.preferredWidth: 22
                                            Layout.preferredHeight: 22
                                            radius: 11
                                            color: C.Theme.alpha(C.Theme.accent, 0.14)
                                            border.color: C.Theme.accent
                                            border.width: 1
                                            Text {
                                                anchors.centerIn: parent
                                                text: model.step
                                                color: C.Theme.accent
                                                font.family: C.Theme.fontMono
                                                font.pixelSize: 10
                                                font.weight: Font.Bold
                                            }
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: model.description
                                            color: C.Theme.textSecondary
                                            font.family: C.Theme.fontSans
                                            font.pixelSize: 12
                                            wrapMode: Text.Wrap
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // ─── LOG FEED ────────────────────────────────────
                C.Card {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    Layout.fillHeight: true
                    title: "Log Feed"
                    subtitle: feedModel.count > 0
                        ? (feedModel.count + " evento(s) · " + root.phaseLabel)
                        : "Aguardando execucao"

                    // Progress bar fininha no header
                    Rectangle {
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.topMargin: 52
                        anchors.leftMargin: 1
                        anchors.rightMargin: 1
                        height: 2
                        color: "transparent"
                        Rectangle {
                            height: parent.height
                            width: Math.max(0, Math.min(100, root.progress)) / 100 * parent.width
                            color: C.Theme.accent
                            Behavior on width { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
                        }
                    }

                    // Estado vazio premium
                    ColumnLayout {
                        anchors.centerIn: parent
                        visible: feedModel.count === 0
                        spacing: 10

                        Item {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            Layout.alignment: Qt.AlignHCenter
                            Rectangle {
                                anchors.fill: parent
                                radius: 12
                                color: C.Theme.alpha(C.Theme.violet, 0.08)
                                border.color: C.Theme.alpha(C.Theme.violet, 0.18)
                                border.width: 1
                            }
                            // Icone de terminal: prompt > _
                            Text {
                                anchors.centerIn: parent
                                text: "> _"
                                color: C.Theme.violet
                                font.family: C.Theme.fontMono
                                font.pixelSize: 16
                                font.weight: Font.Bold
                            }
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Nenhum comando executado."
                            color: C.Theme.textSecondary
                            font.family: C.Theme.fontSans
                            font.pixelSize: 13
                            font.weight: Font.Medium
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "Digite uma tarefa e execute."
                            color: C.Theme.textMuted
                            font.family: C.Theme.fontSans
                            font.pixelSize: 12
                        }
                    }

                    // Feed em tempo real
                    ListView {
                        id: feed
                        anchors.fill: parent
                        anchors.margins: 14
                        anchors.topMargin: 8
                        model: feedModel
                        visible: feedModel.count > 0
                        spacing: 6
                        clip: true
                        onCountChanged: positionViewAtEnd()

                        delegate: Rectangle {
                            width: feed.width
                            radius: C.Theme.rSm
                            color: model.kind === "error"
                                ? C.Theme.alpha(C.Theme.coral, 0.07)
                                : model.kind === "cancel"
                                    ? C.Theme.alpha(C.Theme.amber, 0.07)
                                    : model.kind === "end"
                                        ? C.Theme.alpha(C.Theme.accent, 0.07)
                                        : Qt.rgba(1, 1, 1, 0.02)
                            border.color: Qt.rgba(1, 1, 1, 0.05)
                            border.width: 1
                            implicitHeight: feedCol.implicitHeight + 18

                            ColumnLayout {
                                id: feedCol
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 10
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 7
                                    Rectangle {
                                        width: 6; height: 6; radius: 3
                                        color: model.kind === "error" ? C.Theme.coral
                                            : model.kind === "cancel" ? C.Theme.amber
                                            : model.kind === "end" ? C.Theme.accent
                                            : (model.ok ? C.Theme.violet : C.Theme.coral)
                                    }
                                    C.AgentBadge {
                                        agent: (model.action || "").replace("[","").replace("]","").split(" ")[0]
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: model.desc || ""
                                        color: C.Theme.textPrimary
                                        font.family: C.Theme.fontSans
                                        font.pixelSize: 12
                                        elide: Text.ElideRight
                                    }
                                }
                                Text {
                                    visible: !!model.result
                                    Layout.fillWidth: true
                                    text: model.result || ""
                                    color: C.Theme.textMuted
                                    font.family: C.Theme.fontMono
                                    font.pixelSize: 10
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 4
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
