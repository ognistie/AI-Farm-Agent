import QtQuick
import "."

Rectangle {
    id: root
    property string agent: ""
    readonly property color tone: Theme.agentColor(agent)

    implicitWidth: label.implicitWidth + 16
    implicitHeight: 18
    radius: 4
    color: Theme.alpha(tone, 0.16)
    border.color: Theme.alpha(tone, 0.32)
    border.width: 1

    Text {
        id: label
        anchors.centerIn: parent
        text: (root.agent || "").toUpperCase()
        color: tone
        font.family: Theme.fontMono
        font.pixelSize: Theme.sizeMicro
        font.weight: Font.Medium
        font.letterSpacing: 0.6
    }
}
