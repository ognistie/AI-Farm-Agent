import QtQuick
import "."

Rectangle {
    id: root
    property string text: ""
    property string glyph: ""
    property color tone: Theme.textSecondary
    signal clicked()

    implicitWidth: row.implicitWidth + 20
    implicitHeight: 30
    radius: Theme.rSm
    color: "transparent"
    border.color: Theme.hairline
    border.width: 1

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 6
        Text {
            visible: root.glyph !== ""
            text: root.glyph
            color: root.tone
            font.pixelSize: Theme.sizeMd
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: root.text
            color: root.tone
            font.family: Theme.fontSans
            font.pixelSize: Theme.sizeSm
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
        onEntered: root.color = Theme.bgSurfaceHi
        onExited:  root.color = "transparent"
    }

    Behavior on color { ColorAnimation { duration: 140 } }
}
