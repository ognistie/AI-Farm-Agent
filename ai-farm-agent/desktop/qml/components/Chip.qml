import QtQuick
import "."

Rectangle {
    id: root
    property string text: ""
    property bool selected: false
    property bool hoverable: true
    property color tone: Theme.accent
    signal clicked()

    implicitWidth: label.implicitWidth + 22
    implicitHeight: 30
    radius: Theme.rPill
    color: selected ? Theme.alpha(tone, 0.16) : Theme.bgSurfaceHi
    border.color: selected ? Theme.alpha(tone, 0.55) : Theme.hairline
    border.width: 1

    Text {
        id: label
        anchors.centerIn: parent
        text: root.text
        color: selected ? tone : Theme.textSecondary
        font.family: Theme.fontSans
        font.pixelSize: Theme.sizeSm
        font.weight: selected ? Font.Medium : Font.Normal
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: root.hoverable
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
        onEntered: if (hoverable && !selected) root.color = Qt.lighter(Theme.bgSurfaceHi, 1.18)
        onExited:  if (!selected) root.color = Theme.bgSurfaceHi
    }

    Behavior on color { ColorAnimation { duration: 140 } }
}
