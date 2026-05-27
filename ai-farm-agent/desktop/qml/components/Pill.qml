import QtQuick
import "."

Rectangle {
    id: root
    property string text: ""
    property color tone: Theme.textSecondary
    property bool subtle: true

    implicitWidth: label.implicitWidth + 14
    implicitHeight: 20
    radius: Theme.rPill
    color: subtle ? Theme.alpha(tone, 0.10) : tone
    border.color: subtle ? Theme.alpha(tone, 0.28) : "transparent"
    border.width: 1

    Text {
        id: label
        anchors.centerIn: parent
        text: root.text
        color: subtle ? tone : Theme.textInverse
        font.family: Theme.fontMono
        font.pixelSize: Theme.sizeMicro
        font.letterSpacing: 0.8
        font.weight: Font.Medium
    }
}
