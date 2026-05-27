// Botao — variantes primary (teal solido) / secondary / ghost / danger / mode
// Mode: chip de modo minimalista, so texto, com fundo teal quando selecionado.
import QtQuick
import "."

Rectangle {
    id: root

    property string text: ""
    property string trailing: ""
    property string leading: ""
    property string variant: "primary"   // primary | secondary | ghost | danger | mode
    property bool enabled: true
    property bool selected: false        // usado por variant=mode
    property bool busy: false
    signal clicked()

    readonly property color toneBg: {
        if (!enabled) return Theme.alpha(Theme.textMuted, 0.08)
        switch (variant) {
            case "primary":   return Theme.accent
            case "danger":    return Theme.coral
            case "secondary": return Theme.alpha(Qt.rgba(1,1,1,1), 0.04)
            case "ghost":     return "transparent"
            case "mode":      return selected ? Theme.accent : "transparent"
        }
        return Theme.accent
    }

    readonly property color toneFg: {
        if (!enabled) return Theme.textMuted
        switch (variant) {
            case "primary":   return Theme.textInverse
            case "danger":    return Theme.textInverse
            case "secondary": return Theme.textPrimary
            case "ghost":     return Theme.textSecondary
            case "mode":      return selected ? Theme.textInverse : Theme.textSecondary
        }
        return Theme.textInverse
    }

    readonly property color toneBorder: {
        if (variant === "ghost") return "transparent"
        if (variant === "mode")  return "transparent"
        if (variant === "secondary") return Theme.hairline
        return "transparent"
    }

    implicitWidth: row.implicitWidth + (
        variant === "mode" ? 18
        : (variant === "primary" || variant === "danger") ? 28
        : 22
    )
    implicitHeight: variant === "mode" ? 30 : 34
    radius: variant === "mode" ? Theme.rPill : Theme.rMd
    color: toneBg
    border.color: toneBorder
    border.width: variant === "secondary" ? 1 : 0
    opacity: enabled ? 1.0 : 0.55

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 7

        Text {
            visible: root.leading !== ""
            text: root.leading
            color: root.toneFg
            font.family: Theme.fontMono
            font.pixelSize: Theme.sizeSm
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: root.busy ? "Executando..." : root.text
            color: root.toneFg
            font.family: Theme.fontSans
            font.pixelSize: variant === "mode" ? Theme.sizeSm : Theme.sizeSm
            font.weight: (variant === "primary" || variant === "danger")
                ? Font.DemiBold
                : (variant === "mode" && selected) ? Font.Medium : Font.Normal
            font.letterSpacing: -0.1
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            visible: root.trailing !== ""
            text: root.trailing
            color: root.toneFg
            font.family: Theme.fontMono
            font.pixelSize: Theme.sizeMd
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ForbiddenCursor
        onClicked: if (root.enabled) root.clicked()
        onEntered: if (enabled) {
            if (variant === "primary") root.color = Qt.lighter(Theme.accent, 1.08)
            else if (variant === "danger") root.color = Qt.lighter(Theme.coral, 1.08)
            else if (variant === "mode" && !selected) root.color = Qt.rgba(1,1,1,0.04)
            else if (variant !== "mode") root.color = Theme.bgSurfaceHi
        }
        onExited: root.color = toneBg
        onPressed: if (enabled) root.opacity = 0.85
        onReleased: root.opacity = enabled ? 1.0 : 0.55
    }

    Behavior on color { ColorAnimation { duration: 130 } }
    Behavior on opacity { NumberAnimation { duration: 130 } }
}
