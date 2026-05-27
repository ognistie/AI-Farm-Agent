import QtQuick
import "."

Rectangle {
    id: root
    property real value: 0
    property color tone: Theme.accent
    implicitHeight: 4
    radius: 2
    color: Theme.bgInput

    Rectangle {
        height: parent.height
        radius: 2
        width: Math.max(0, Math.min(100, root.value)) / 100 * parent.width
        color: tone
        Behavior on width { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
    }
}
