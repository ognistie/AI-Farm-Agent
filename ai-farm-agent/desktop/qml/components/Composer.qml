// Caixa de entrada da tarefa. Enter envia, Shift+Enter quebra linha.
// Cresce ate ~6 linhas e depois rola. Opcoes ficam dentro da caixa.
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

    signal submitted(string task)
    signal stopRequested()

    function focusInput() { input.forceActiveFocus(); input.cursorPosition = input.length }

    readonly property bool canSend: !running && input.text.trim().length > 0

    function send() {
        if (!canSend) return
        submitted(input.text.trim())
    }

    implicitHeight: body.implicitHeight + 24
    radius: Theme.rLg
    color: Theme.bgSurface
    border.width: 1
    border.color: input.activeFocus ? Theme.hairlineHi : Theme.hairline
    Behavior on border.color { ColorAnimation { duration: Theme.durFast } }

    ColumnLayout {
        id: body
        anchors.fill: parent
        anchors.margins: 12
        anchors.leftMargin: 16
        spacing: 8

        ScrollView {
            id: scroller
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(Math.max(input.implicitHeight, 24), 140)
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            TextArea {
                id: input
                placeholderText: root.placeholder
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

            Item { Layout.fillWidth: true }

            Text {
                visible: !root.running && input.activeFocus && input.length > 0
                text: "Shift+Enter nova linha"
                color: Theme.textTertiary
                font.family: Theme.fontSans
                font.pixelSize: Theme.sizeXs
                Layout.rightMargin: 6
            }

            // Enviar / Parar
            Rectangle {
                id: sendBtn
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
