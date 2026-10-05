// Caixa de entrada da tarefa. Enter envia, Shift+Enter quebra linha.
// Cresce ate ~6 linhas e depois rola. Opcoes ficam dentro da caixa.
// Voz: o microfone grava uma mensagem de audio (clica, fala, envia);
// "Conversa" deixa o microfone aberto e cada fala vira pedido.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property alias text: input.text
    property bool running: false
    property alias dryRun: simulatePill.checked
    property alias genReport: reportPill.checked
    property string placeholder: "Descreva uma tarefa..."
    // Voz: idle | recording | listening | thinking | speaking
    property string voiceState: "idle"
    property real voiceLevel: 0
    property bool liveOn: false
    property int queued: 0
    property double recStartedAt: 0
    property string voiceHotkey: "Ctrl+Alt+V"
    readonly property bool recording: voiceState === "recording"

    signal submitted(string task)
    signal stopRequested()
    signal micClicked()
    signal recordCancel()
    signal liveSwitched(bool on)

    function focusInput() { input.forceActiveFocus(); input.cursorPosition = input.length }

    readonly property bool canSend: !running && input.text.trim().length > 0

    function send() {
        if (!canSend) return
        submitted(input.text.trim())
    }

    property int recSeconds: 0
    Timer {
        interval: 250; repeat: true; running: root.recording
        onTriggered: root.recSeconds = Math.floor((Date.now() - root.recStartedAt) / 1000)
    }

    implicitHeight: body.implicitHeight + 24
    radius: Theme.rLg
    color: Theme.bgSurface
    border.width: 1
    border.color: root.recording ? Theme.alpha(Theme.danger, 0.5)
                : input.activeFocus ? Theme.hairlineHi : Theme.hairline
    Behavior on border.color { ColorAnimation { duration: Theme.durFast } }

    ColumnLayout {
        id: body
        anchors.fill: parent
        anchors.margins: 12
        anchors.leftMargin: 16
        spacing: 8

        // Texto (ou, gravando, a barra da mensagem de audio)
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(Math.max(input.implicitHeight, 24), 140)

            ScrollView {
                id: scroller
                anchors.fill: parent
                visible: !root.recording
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                TextArea {
                    id: input
                    placeholderText: root.liveOn ? "Conversa ao vivo: pode falar (ou digitar)..." : root.placeholder
                    placeholderTextColor: Theme.textTertiary
                    color: Theme.textPrimary
                    selectionColor: Theme.alpha(Theme.info, 0.35)
                    selectedTextColor: Theme.textPrimary
                    font.family: Theme.fontSans
                    font.pixelSize: 15
                    wrapMode: TextArea.Wrap
                    background: null
                    padding: 0
                    topPadding: 4
                    readOnly: root.running

                    Keys.onPressed: (event) => {
                        if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter)
                                && !(event.modifiers & Qt.ShiftModifier)) {
                            event.accepted = true
                            root.send()
                        }
                    }
                    Accessible.name: "Tarefa"
                }
            }

            RowLayout {
                anchors.fill: parent
                visible: root.recording
                spacing: 10

                Rectangle {
                    width: 10; height: 10; radius: 5
                    color: Theme.danger
                    SequentialAnimation on opacity {
                        running: root.recording; loops: Animation.Infinite
                        NumberAnimation { to: 0.25; duration: 600 }
                        NumberAnimation { to: 1.0; duration: 600 }
                    }
                }
                Text {
                    text: Math.floor(root.recSeconds / 60) + ":" + ("0" + (root.recSeconds % 60)).slice(-2)
                    color: Theme.textPrimary
                    font.family: Theme.fontSans
                    font.pixelSize: 15
                    font.features: { "tnum": 1 }
                }
                // Barras de volume
                Row {
                    spacing: 3
                    Repeater {
                        model: 18
                        Rectangle {
                            width: 3
                            radius: 1.5
                            anchors.verticalCenter: parent.verticalCenter
                            height: 4 + 16 * Math.max(0, Math.min(1, root.voiceLevel * (0.55 + 0.45 * Math.abs(Math.sin(index * 1.7)))))
                            color: Theme.alpha(Theme.danger, 0.75)
                            Behavior on height { NumberAnimation { duration: 80 } }
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: "Gravando — clique em enviar quando terminar"
                    color: Theme.textTertiary
                    font.family: Theme.fontSans
                    font.pixelSize: Theme.sizeSm
                    elide: Text.ElideRight
                }
                Text {
                    text: "Cancelar"
                    color: cancelMouse.containsMouse ? Theme.textPrimary : Theme.textSecondary
                    font.family: Theme.fontSans
                    font.pixelSize: Theme.sizeSm
                    MouseArea {
                        id: cancelMouse
                        anchors.fill: parent
                        anchors.margins: -6
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.recordCancel()
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            TogglePill {
                id: simulatePill
                text: "Simular"
                icon: ""
                tooltip: "Mostra o plano sem executar nada no computador"
            }
            TogglePill {
                id: reportPill
                text: "Relatório"
                icon: ""
                tooltip: "Gera um resumo da execução ao final (1 chamada extra de IA)"
            }
            TogglePill {
                id: livePill
                text: "Conversa"
                icon: ""
                tooltip: "Microfone aberto: fale à vontade, cada pedido é executado em seguida"
                checked: root.liveOn
                // O estado real vem do backend; o clique so pede a troca
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.liveSwitched(!root.liveOn)
                }
            }

            Item { Layout.fillWidth: true }

            Text {
                visible: text !== ""
                text: root.voiceState === "thinking" ? "Entendendo..."
                    : root.voiceState === "speaking" ? "Falando..."
                    : root.liveOn && root.voiceState === "listening"
                      ? "Ouvindo" + (root.queued > 0 ? " · " + root.queued + " na fila" : "")
                    : (!root.running && input.activeFocus && input.length > 0) ? "Shift+Enter nova linha"
                    : ""
                color: root.liveOn && root.voiceState === "listening" ? Theme.danger : Theme.textTertiary
                font.family: Theme.fontSans
                font.pixelSize: Theme.sizeXs
                Layout.rightMargin: 4
            }

            // Microfone: grava a mensagem de audio; gravando, vira "enviar audio"
            Rectangle {
                id: micBtn
                visible: !root.liveOn
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                radius: 17
                color: root.recording ? Theme.danger
                     : (micMouse.containsMouse ? Theme.bgHover : "transparent")
                border.width: root.recording ? 0 : 1
                border.color: Theme.hairline

                Rectangle {
                    anchors.centerIn: parent
                    visible: root.recording
                    width: parent.width + 12 * root.voiceLevel
                    height: width
                    radius: width / 2
                    color: "transparent"
                    border.width: 2
                    border.color: Theme.alpha(Theme.danger, 0.35)
                    Behavior on width { NumberAnimation { duration: 90 } }
                }
                Spinner {
                    anchors.centerIn: parent
                    visible: root.voiceState === "thinking" && !root.recording
                    size: 14
                }
                Icon {
                    anchors.centerIn: parent
                    visible: !(root.voiceState === "thinking" && !root.recording)
                    glyph: root.recording ? "" : ""
                    size: 14
                    color: root.recording ? Theme.textInverse : Theme.textSecondary
                }
                MouseArea {
                    id: micMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.micClicked()
                }
                ToolTipHint {
                    text: root.recording ? "Enviar áudio" : "Gravar áudio (" + root.voiceHotkey + ")"
                    shown: micMouse.containsMouse
                }
                Accessible.role: Accessible.Button
                Accessible.name: root.recording ? "Enviar áudio" : "Gravar áudio"
            }

            // Enviar / Parar
            Rectangle {
                id: sendBtn
                visible: !root.recording
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                radius: 17
                color: root.running ? Theme.bgSurfaceHi
                     : (root.canSend ? Theme.primary : Theme.bgSurfaceHi)
                border.width: root.running ? 1 : 0
                border.color: Theme.hairlineHi
                Behavior on color { ColorAnimation { duration: Theme.durFast } }

                Icon {
                    anchors.centerIn: parent
                    glyph: root.running ? "" : ""
                    size: root.running ? 12 : 14
                    color: root.running ? Theme.textPrimary
                         : (root.canSend ? Theme.textInverse : Theme.textTertiary)
                }
                MouseArea {
                    id: sendMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: (root.running || root.canSend) ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: root.running ? root.stopRequested() : root.send()
                }
                ToolTipHint {
                    text: root.running ? "Parar execução (Esc)" : "Executar (Enter)"
                    shown: sendMouse.containsMouse
                }
                Accessible.role: Accessible.Button
                Accessible.name: root.running ? "Parar" : "Executar"
            }
        }
    }
}
