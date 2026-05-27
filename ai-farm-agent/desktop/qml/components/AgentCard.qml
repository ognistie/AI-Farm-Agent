// Card de agente: nome, funcao, status, atividade atual, mini progresso.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: root

    property string name: ""
    property string role: ""
    property string status: "idle"     // online | idle | running | waiting | error
    property string activity: ""
    property string model: ""
    property string glyph: "◇"
    property real load: 0              // 0..100 — mini progresso

    color: Theme.bgSurface
    radius: Theme.rLg
    border.color: status === "running" ? Theme.alpha(Theme.accent, 0.45) : Theme.hairline
    border.width: 1
    implicitHeight: 156

    // Glow ao ficar running
    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        border.width: 1
        border.color: status === "running"
            ? Theme.alpha(Theme.accent, 0.18) : "transparent"
        z: -1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                width: 32; height: 32; radius: 8
                color: Theme.alpha(Theme.agentColor(name), 0.16)
                border.color: Theme.alpha(Theme.agentColor(name), 0.30)
                border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: root.glyph
                    color: Theme.agentColor(name)
                    font.pixelSize: 14
                }
            }
            ColumnLayout {
                spacing: 2
                Layout.fillWidth: true
                Text {
                    text: root.name
                    color: Theme.textPrimary
                    font.family: Theme.fontSans
                    font.pixelSize: Theme.sizeMd
                    font.weight: Font.DemiBold
                }
                Text {
                    text: root.model
                    color: Theme.textMuted
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.sizeMicro
                    font.letterSpacing: 0.8
                }
            }
            StatusBadge { status: root.status; label: root.status }
        }

        Text {
            Layout.fillWidth: true
            text: root.role
            color: Theme.textSecondary
            font.family: Theme.fontSans
            font.pixelSize: Theme.sizeSm
            wrapMode: Text.Wrap
            lineHeight: 1.35
            elide: Text.ElideRight
            maximumLineCount: 2
        }

        Item { Layout.fillHeight: true }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "ATIVIDADE"
                    color: Theme.textMuted
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.sizeMicro
                    font.letterSpacing: 1
                }
                Item { Layout.fillWidth: true }
                Text {
                    text: Math.round(root.load) + "%"
                    color: Theme.textSecondary
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.sizeMicro
                }
            }
            ProgressBar {
                Layout.fillWidth: true
                Layout.preferredHeight: 4
                value: root.load
                tone: Theme.agentColor(name)
            }
            Text {
                visible: root.activity !== ""
                Layout.fillWidth: true
                text: root.activity
                color: Theme.textSecondary
                font.family: Theme.fontMono
                font.pixelSize: Theme.sizeXs
                elide: Text.ElideRight
            }
        }
    }
}
