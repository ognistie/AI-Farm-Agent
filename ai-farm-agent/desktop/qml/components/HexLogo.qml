import QtQuick
import "."

Item {
    id: root
    property color tone: Theme.accent
    property int sizePx: 22
    property bool spinning: false
    implicitWidth: sizePx
    implicitHeight: sizePx

    Text {
        anchors.centerIn: parent
        text: "⬡"
        font.pixelSize: sizePx
        color: tone
        RotationAnimation on rotation {
            running: spinning
            loops: Animation.Infinite
            from: 0; to: 360; duration: 3600
        }
    }
}
