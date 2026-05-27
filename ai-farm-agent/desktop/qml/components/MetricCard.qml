// Card de metrica — minimalista, hairline tenue, icone discreto, numero hero.
// Estetica Claude/Lanes.sh: tipografia premium, espaco em branco generoso.
import QtQuick
import QtQuick.Layouts
import "."

Rectangle {
    id: root

    property string value: "0"
    property string label: ""
    property string unit: ""
    property string glyph: ""
    property color accentColor: Theme.accent

    color: Qt.rgba(0.071, 0.075, 0.086, 0.72)
    radius: Theme.rLg
    border.color: Qt.rgba(1, 1, 1, 0.05)
    border.width: 1
    implicitHeight: 104

    // Top highlight 1px
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 1
        height: 1
        radius: parent.radius
        color: Qt.rgba(1, 1, 1, 0.04)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Item {
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                Rectangle {
                    anchors.fill: parent
                    radius: 6
                    color: Theme.alpha(accentColor, 0.12)
                    border.color: Theme.alpha(accentColor, 0.22)
                    border.width: 1
                }
                Text {
                    anchors.centerIn: parent
                    text: root.glyph
                    color: accentColor
                    font.pixelSize: 12
                }
            }

            Text {
                text: root.label
                color: Theme.textSecondary
                font.family: Theme.fontSans
                font.pixelSize: Theme.sizeSm
                font.weight: Font.Medium
                Layout.alignment: Qt.AlignVCenter
            }
            Item { Layout.fillWidth: true }
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 5
            Text {
                text: root.value
                color: Theme.textPrimary
                font.family: Theme.fontSans
                font.pixelSize: 26
                font.weight: Font.Bold
                font.letterSpacing: -0.6
            }
            Text {
                visible: root.unit !== ""
                text: root.unit
                color: Theme.textMuted
                font.family: Theme.fontSans
                font.pixelSize: Theme.sizeSm
                Layout.alignment: Qt.AlignBottom
                bottomPadding: 5
            }
            Item { Layout.fillWidth: true }
        }
    }
}
