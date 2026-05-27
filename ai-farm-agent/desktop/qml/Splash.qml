// Boas-vindas — minimalismo extremo estilo Claude/Anthropic.
// APENAS: titulo + credito github. Halo teal radial muito sutil ao fundo.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components" as C

Rectangle {
    id: root
    color: C.Theme.bgBase
    signal enterRequested()
    clip: true

    // Halo teal radial — SUTIL, atras do hexagono central.
    // Tamanho proporcional pequeno (40% da menor dimensao) para nao
    // dominar a tela inteira.
    Rectangle {
        anchors.centerIn: parent
        width:  Math.min(420, Math.min(parent.width, parent.height) * 0.55)
        height: width
        radius: width / 2
        opacity: 0.07
        gradient: Gradient {
            GradientStop { position: 0.0; color: C.Theme.accent }
            GradientStop { position: 0.6; color: "transparent" }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 22
        width: Math.min(640, parent.width - 80)

        C.HexLogo {
            Layout.alignment: Qt.AlignHCenter
            sizePx: 52
            tone: C.Theme.accent
            opacity: 0.92
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: "Bem-vindo ao AI Farm Agents"
            color: C.Theme.textPrimary
            font.family: C.Theme.fontSans
            font.pixelSize: 32
            font.weight: Font.DemiBold
            font.letterSpacing: -0.6
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                radius: 12
                color: C.Theme.textPrimary
                Text {
                    anchors.centerIn: parent
                    text: ""
                    color: C.Theme.bgBase
                    font.family: "Segoe Fluent Icons, Segoe MDL2 Assets"
                    font.pixelSize: 14
                }
                Text {
                    visible: parent.children[0].paintedWidth < 4
                    anchors.centerIn: parent
                    text: "GH"
                    color: C.Theme.bgBase
                    font.family: C.Theme.fontMono
                    font.pixelSize: 10
                    font.weight: Font.Bold
                }
            }

            Text {
                text: "desenvolvido por"
                color: C.Theme.textMuted
                font.family: C.Theme.fontSans
                font.pixelSize: 13
                Layout.alignment: Qt.AlignVCenter
            }

            Text {
                text: "ognistie"
                color: C.Theme.accent
                font.family: C.Theme.fontMono
                font.pixelSize: 13
                font.weight: Font.Medium
                Layout.alignment: Qt.AlignVCenter

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onClicked: Qt.openUrlExternally("https://github.com/ognistie")
                    onEntered: parent.font.underline = true
                    onExited: parent.font.underline = false
                }
            }
        }

        Item { Layout.preferredHeight: 16 }
        C.ActionButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 220
            Layout.preferredHeight: 42
            text: "Iniciar"
            trailing: "→"
            onClicked: root.enterRequested()
        }
    }

    opacity: 0
    Component.onCompleted: fadeIn.start()
    NumberAnimation on opacity {
        id: fadeIn; from: 0; to: 1; duration: 500; easing.type: Easing.OutCubic
    }
}
