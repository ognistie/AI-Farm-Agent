// Item da sidebar: icone + rotulo, estado ativo com fundo sutil.
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    property string label: ""
    property string icon: ""
    property bool active: false
    property bool muted: false      // itens secundarios (ex.: recentes)
    signal clicked()

    implicitHeight: 34
    radius: Theme.rSm
    color: active ? Theme.bgPressed : (mouse.containsMouse ? Theme.bgHover : "transparent")
    Behavior on color { ColorAnimation { duration: Theme.durFast } }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 10

        Icon {
            visible: root.icon !== ""
            glyph: root.icon
            size: 15
            color: root.active ? Theme.textPrimary : Theme.textSecondary
            Layout.preferredWidth: 18
        }
        Text {
            Layout.fillWidth: true
            text: root.label
            elide: Text.ElideRight
            color: root.active ? Theme.textPrimary
                               : (root.muted ? Theme.textSecondary : Theme.textPrimary)
            font.family: Theme.fontSans
            font.pixelSize: 13
            font.weight: root.active ? Font.Medium : Font.Normal
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    Accessible.role: Accessible.Button
    Accessible.name: root.label
}
