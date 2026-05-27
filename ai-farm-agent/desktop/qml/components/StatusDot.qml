import QtQuick
import "."

Item {
    id: root
    property color tone: Theme.accent
    property bool pulsing: true
    implicitWidth: 8
    implicitHeight: 8

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: tone
    }
    Rectangle {
        visible: pulsing
        anchors.centerIn: parent
        width: parent.width; height: parent.height
        radius: width / 2
        color: "transparent"
        border.color: tone
        border.width: 1
        opacity: 0.6
        SequentialAnimation on scale {
            running: pulsing
            loops: Animation.Infinite
            NumberAnimation { from: 1.0; to: 2.8; duration: 1500; easing.type: Easing.OutCubic }
            PauseAnimation { duration: 120 }
        }
        SequentialAnimation on opacity {
            running: pulsing
            loops: Animation.Infinite
            NumberAnimation { from: 0.6; to: 0.0; duration: 1500; easing.type: Easing.OutCubic }
            PauseAnimation { duration: 120 }
        }
    }
}
