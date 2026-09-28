// Opcao liga/desliga compacta (ex.: "Simular" dentro do composer).
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    property string text: ""
    property string icon: ""
    property bool checked: false
    property string tooltip: ""

    implicitWidth: row.implicitWidth + 20
    implicitHeight: 28
    radius: height / 2
    color: checked ? Theme.alpha(Theme.primary, 0.12)
                   : (mouse.containsMouse ? Theme.bgHover : "transparent")
    border.width: 1
    border.color: checked ? Theme.alpha(Theme.primary, 0.35) : Theme.hairline
    Behavior on color { ColorAnimation { duration: Theme.durFast } }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 6
        Icon {
            visible: root.icon !== ""
            glyph: root.icon
            size: 12
            color: root.checked ? Theme.textPrimary : Theme.textSecondary
        }
        Text {
            text: root.text
            color: root.checked ? Theme.textPrimary : Theme.textSecondary
            font.family: Theme.fontSans
            font.pixelSize: Theme.sizeSm
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.checked = !root.checked
    }

    ToolTipHint { text: root.tooltip; shown: mouse.containsMouse && root.tooltip !== "" }

    Accessible.role: Accessible.CheckBox
    Accessible.name: root.text
    Accessible.checked: root.checked
}
