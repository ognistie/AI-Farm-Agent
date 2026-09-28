// Tooltip leve com atraso, desenhado acima do item pai.
import QtQuick
import QtQuick.Controls

ToolTip {
    id: tip
    property bool shown: false
    visible: shown && text !== ""
    delay: 500
    timeout: 6000

    contentItem: Text {
        text: tip.text
        color: Theme.textPrimary
        font.family: Theme.fontSans
        font.pixelSize: Theme.sizeSm
        wrapMode: Text.Wrap
    }
    background: Rectangle {
        color: Theme.bgSurfaceHi
        radius: Theme.rSm
        border.width: 1
        border.color: Theme.hairline
    }
}
