// Item da sidebar — ultra minimalista, icone fino + label nitido.
import QtQuick
import "."

Rectangle {
    id: root
    property string label: ""
    property string glyph: "⌂"
    property bool active: false
    signal clicked()

    implicitHeight: 34
    radius: Theme.rSm
    color: active ? Theme.alpha(Theme.accent, 0.10) : "transparent"

    Row {
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        Item {
            width: 14; height: 14
            anchors.verticalCenter: parent.verticalCenter
            Text {
                anchors.centerIn: parent
                text: glyph
                color: active ? Theme.accent : Theme.textMuted
                font.pixelSize: 14
            }
        }
        Text {
            text: label
            color: active ? Theme.textPrimary : Theme.textSecondary
            font.family: Theme.fontSans
            font.pixelSize: Theme.sizeSm
            font.weight: active ? Font.Medium : Font.Normal
            font.letterSpacing: -0.1
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        onClicked: root.clicked()
        onEntered: if (!active) root.color = Qt.rgba(1, 1, 1, 0.025)
        onExited:  if (!active) root.color = "transparent"
    }

    Behavior on color { ColorAnimation { duration: 140 } }
}
