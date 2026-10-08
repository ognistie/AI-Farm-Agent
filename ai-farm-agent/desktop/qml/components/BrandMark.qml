// Marca do app: quatro quadrados arredondados, o de baixo a direita no
// azul de destaque (um agente em acao entre os outros).
import QtQuick

Item {
    id: root
    property int sizePx: 18
    property color tone: Theme.textPrimary
    property color highlight: Theme.accent

    implicitWidth: sizePx
    implicitHeight: sizePx

    readonly property real gap: Math.max(1.5, sizePx * 0.12)
    readonly property real cell: (sizePx - gap) / 2

    Repeater {
        model: 4
        Rectangle {
            x: (index % 2) * (root.cell + root.gap)
            y: Math.floor(index / 2) * (root.cell + root.gap)
            width: root.cell
            height: root.cell
            radius: root.cell * 0.28
            antialiasing: true
            color: index === 3 ? root.highlight : root.tone
        }
    }
}
