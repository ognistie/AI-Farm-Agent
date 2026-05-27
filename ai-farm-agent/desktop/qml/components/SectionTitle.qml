import QtQuick
import QtQuick.Layouts
import "."

Item {
    id: root
    property string text: ""
    property string sub: ""
    property string eyebrow: ""

    implicitHeight: col.implicitHeight

    ColumnLayout {
        id: col
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 4

        Text {
            visible: root.eyebrow !== ""
            text: root.eyebrow.toUpperCase()
            color: Theme.accent
            font.family: Theme.fontMono
            font.pixelSize: Theme.sizeMicro
            font.letterSpacing: 1.8
        }
        Text {
            text: root.text
            color: Theme.textPrimary
            font.family: Theme.fontSans
            font.pixelSize: Theme.sizeXxl
            font.weight: Font.DemiBold
        }
        Text {
            visible: root.sub !== ""
            Layout.fillWidth: true
            text: root.sub
            color: Theme.textSecondary
            font.family: Theme.fontSans
            font.pixelSize: Theme.sizeSm
            wrapMode: Text.Wrap
        }
    }
}
