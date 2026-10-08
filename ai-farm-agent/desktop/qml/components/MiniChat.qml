// Mini chat: quando o agente vai para outra janela (abre um app, o
// navegador...), a conversa atual fica num cartao no canto inferior direito.
//
// Enquanto a tarefa roda ele e "passivo": nao recebe foco nem cliques, para
// nao atrapalhar o que o agente digita e clica (parar: atalho global,
// Ctrl+Alt+X por padrao). Quando a tarefa termina ele volta a ser
// interativo e da para continuar a conversa.
//
// O estado vem da TaskView (`view`); o Python posiciona e alterna o modo.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: mini
    objectName: "miniChat"

    property var view: null
    property string stopHotkey: ""   // atalho global de parar (vazio se indisponivel)
    readonly property bool passive: !!view && view.running

    signal expandRequested()
    signal closeRequested()

    width: 380
    height: 560
    visible: false
    // Janela independente: se fosse "filha" da principal, o Windows a
    // esconderia junto quando a principal minimiza
    transientParent: null
    color: Theme.bgBase
    title: "AI Farm Agent"
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
           | (passive ? (Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus) : 0)

    function scrollSoon() { scrollTimer.restart() }
    Timer { id: scrollTimer; interval: 40; onTriggered: body.scrollToEnd() }

    Connections {
        target: mini.view
        ignoreUnknownSignals: true
        function onStatusChanged() { mini.scrollSoon() }
        function onAssistantTextChanged() { mini.scrollSoon() }
    }
    Connections {
        target: mini.view ? mini.view.steps : null
        ignoreUnknownSignals: true
        function onCountChanged() { mini.scrollSoon() }
    }
    onVisibleChanged: if (visible) scrollSoon()

    Rectangle {
        anchors.fill: parent
        color: Theme.bgBase
        border.width: 1
        border.color: Theme.hairline

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 1
            spacing: 0

            // ── Cabecalho (arrasta a janela) ─────────────────────────
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 44

                DragHandler {
                    target: null
                    onActiveChanged: if (active) mini.startSystemMove()
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 6
                    spacing: 8

                    BrandMark { sizePx: 14 }
                    Text {
                        text: "AI Farm Agent"
                        color: Theme.textPrimary
                        font.family: Theme.fontSans
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    Spinner { visible: mini.passive; size: 12 }
                    Text {
                        visible: mini.passive
                        text: "Executando"
                        color: Theme.textTertiary
                        font.family: Theme.fontSans
                        font.pixelSize: Theme.sizeSm
                        Layout.rightMargin: 4
                    }
                    HeaderButton {
                        visible: !mini.passive
                        glyph: ""
                        tip: "Abrir a janela completa"
                        onClicked: mini.expandRequested()
                    }
                    HeaderButton {
                        visible: !mini.passive
                        glyph: ""
                        tip: "Fechar o mini chat"
                        onClicked: mini.closeRequested()
                    }
                }
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width; height: 1
                    color: Theme.hairline
                }
            }

            // ── Conversa ────────────────────────────────────────────
            ScrollPage {
                id: body
                Layout.fillWidth: true
                Layout.fillHeight: true
                maxWidth: 10000
                sidePadding: 16
                topPadding: 14
                bottomPadding: 10
                spacing: 12

                // Pedidos anteriores: o que foi dito + resultado em uma linha
                Repeater {
                    model: mini.view ? mini.view.turns : null
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        UserBubble { text: model.said }
                        ResultLine { status: model.status; text: model.summary }
                    }
                }

                // Pedido atual
                UserBubble {
                    visible: !!mini.view && !mini.view.idle
                    text: mini.view ? mini.view.task : ""
                }
                Caption {
                    visible: !!mini.view && mini.view.heardText !== ""
                    text: "Ouvi: “" + (mini.view ? mini.view.heardText : "") + "”"
                }
                Caption {
                    visible: !!mini.view && mini.view.resolvedText !== ""
                    text: "Entendi: " + (mini.view ? mini.view.resolvedText : "")
                }

                // Falas do assistente (voz)
                Repeater {
                    model: mini.view ? mini.view.replies : null
                    delegate: RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Row {
                            spacing: 2
                            Layout.alignment: Qt.AlignTop
                            Layout.topMargin: 4
                            Repeater {
                                model: 4
                                Rectangle {
                                    width: 2.5; radius: 1.25
                                    height: [6, 10, 7, 11][index]
                                    anchors.verticalCenter: parent.verticalCenter
                                    color: Theme.accent
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: model.text
                            color: Theme.textPrimary
                            font.family: Theme.fontSans
                            font.pixelSize: 13
                            wrapMode: Text.Wrap
                        }
                    }
                }

                // Passos
                Repeater {
                    model: mini.view ? mini.view.steps : null
                    delegate: RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Item {
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                            Layout.alignment: Qt.AlignTop
                            Spinner { anchors.centerIn: parent; visible: model.state === "running"; size: 12 }
                            StatusDot { anchors.centerIn: parent; visible: model.state !== "running"; status: model.state }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: model.desc
                            color: model.kind === "note" ? Theme.textSecondary : Theme.textPrimary
                            font.family: Theme.fontSans
                            font.pixelSize: 13
                            wrapMode: Text.Wrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                        }
                    }
                }

                // Andamento (antes do primeiro passo: "Entendendo o pedido"...)
                RowLayout {
                    visible: !!mini.view && mini.view.running && mini.view.steps.count === 0
                    Layout.fillWidth: true
                    spacing: 8
                    Spinner { size: 12 }
                    Text {
                        Layout.fillWidth: true
                        text: (mini.view ? mini.view.phaseMsg : "") + "..."
                        color: Theme.textSecondary
                        font.family: Theme.fontSans
                        font.pixelSize: Theme.sizeSm
                        elide: Text.ElideRight
                    }
                }

                // Resultado
                Text {
                    visible: text !== "" && !!mini.view && !mini.view.running
                    Layout.fillWidth: true
                    text: !mini.view ? ""
                        : mini.view.assistantText || mini.view.reportSummary
                          || mini.view.question || (mini.view.status === "failed" ? mini.view.errorMsg : "")
                    color: Theme.textPrimary
                    font.family: Theme.fontSans
                    font.pixelSize: 13
                    lineHeight: 1.25
                    wrapMode: Text.Wrap
                    maximumLineCount: 8
                    elide: Text.ElideRight
                }
                Rectangle {
                    visible: !!mini.view && !mini.view.running && !mini.view.idle && !!mini.view.finalMetrics
                    implicitWidth: costText.implicitWidth + 16
                    implicitHeight: 22
                    radius: 6
                    color: Theme.bgSurfaceHi
                    Text {
                        id: costText
                        anchors.centerIn: parent
                        text: mini.view ? mini.view.usageLine() : ""
                        color: Theme.textSecondary
                        font.family: Theme.fontSans
                        font.pixelSize: Theme.sizeXs
                    }
                }
            }

            // ── Entrada ─────────────────────────────────────────────
            Composer {
                id: miniComposer
                Layout.fillWidth: true
                Layout.margins: 10
                Layout.topMargin: 4
                compact: true
                running: !!mini.view && mini.view.running
                placeholder: !running ? "Peça por texto ou voz..."
                           : mini.stopHotkey ? "Executando... " + mini.stopHotkey + " para parar"
                           : "Executando..."
                voiceState: mini.view ? mini.view.composer.voiceState : "idle"
                voiceLevel: mini.view ? mini.view.composer.voiceLevel : 0
                liveOn: mini.view ? mini.view.composer.liveOn : false
                queued: mini.view ? mini.view.composer.queued : 0
                recStartedAt: mini.view ? mini.view.composer.recStartedAt : 0
                voiceHotkey: mini.view ? mini.view.composer.voiceHotkey : "Ctrl+Alt+V"
                onSubmitted: (t) => { text = ""; mini.view.start(t) }
                onStopRequested: Bridge.forceStop()
                onMicClicked: Bridge.voiceRecordToggle()
                onRecordCancel: Bridge.voiceRecordCancel()
                onLiveSwitched: (on) => Bridge.setLiveConversation(on)
            }
        }
    }

    // ── Pecas locais ────────────────────────────────────────────────
    component UserBubble: Rectangle {
        property alias text: bubbleText.text
        Layout.alignment: Qt.AlignRight
        Layout.maximumWidth: body.width * 0.82
        implicitWidth: Math.min(bubbleText.implicitWidth + 26, body.width * 0.82)
        implicitHeight: bubbleText.implicitHeight + 16
        radius: 16
        color: Theme.bgSurfaceHi
        Text {
            id: bubbleText
            anchors.fill: parent
            anchors.leftMargin: 13; anchors.rightMargin: 13
            anchors.topMargin: 8; anchors.bottomMargin: 8
            color: Theme.textPrimary
            font.family: Theme.fontSans
            font.pixelSize: 13
            wrapMode: Text.Wrap
            textFormat: Text.PlainText
        }
    }

    component Caption: Text {
        Layout.fillWidth: true
        color: Theme.textTertiary
        font.family: Theme.fontSans
        font.pixelSize: Theme.sizeSm
        wrapMode: Text.Wrap
        maximumLineCount: 2
        elide: Text.ElideRight
    }

    component ResultLine: Rectangle {
        id: rl
        property string status: "done"
        property alias text: resultText.text
        Layout.fillWidth: true
        implicitHeight: resultRow.implicitHeight + 16
        radius: 10
        color: Theme.bgBase
        border.width: 1
        border.color: Theme.hairline
        RowLayout {
            id: resultRow
            anchors.fill: parent
            anchors.margins: 8
            anchors.leftMargin: 10
            spacing: 8
            StatusDot { status: rl.status; Layout.alignment: Qt.AlignTop; Layout.topMargin: 1 }
            Text {
                id: resultText
                Layout.fillWidth: true
                color: Theme.textPrimary
                font.family: Theme.fontSans
                font.pixelSize: Theme.sizeSm + 1
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
        }
    }

    component HeaderButton: Rectangle {
        id: hb
        property string glyph: ""
        property string tip: ""
        signal clicked()
        width: 30; height: 30; radius: 8
        color: hbMouse.containsMouse ? Theme.bgHover : "transparent"
        Icon { anchors.centerIn: parent; glyph: hb.glyph; size: 11; color: Theme.textSecondary }
        MouseArea {
            id: hbMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: hb.clicked()
        }
        ToolTipHint { text: hb.tip; shown: hbMouse.containsMouse }
        Accessible.role: Accessible.Button
        Accessible.name: hb.tip
    }
}
