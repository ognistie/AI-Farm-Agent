// Chip discreto colorido para status (Online / Idle / Running / Waiting / Error).
import QtQuick
import "."

Rectangle {
    id: root
    property string status: "idle"
    property string label: status
    property bool dot: true

    readonly property color tone: Theme.statusColor(status)

    implicitWidth: row.implicitWidth + 18
    implicitHeight: 22
    radius: Theme.rPill
    color: Theme.alpha(tone, 0.12)
    border.color: Theme.alpha(tone, 0.30)
    border.width: 1

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6

        Rectangle {
            visible: root.dot
            width: 6; height: 6; radius: 3
            color: tone
            anchors.verticalCenter: parent.verticalCenter

            SequentialAnimation on opacity {
                running: root.status.toLowerCase() === "running"
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.35; duration: 800; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.35; to: 1.0; duration: 800; easing.type: Easing.InOutSine }
            }
        }
        Text {
            text: root.label.toUpperCase()
            color: tone
            font.family: Theme.fontMono
            font.pixelSize: Theme.sizeMicro
            font.letterSpacing: 1
            font.weight: Font.Medium
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
