// Indicador de atividade: arco girando.
import QtQuick

Item {
    id: root
    property int size: 14
    property color color: Theme.textSecondary
    property bool running: true

    implicitWidth: size
    implicitHeight: size

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            ctx.lineWidth = Math.max(1.5, root.size / 9)
            ctx.lineCap = "round"
            ctx.strokeStyle = root.color
            const r = (root.size - ctx.lineWidth) / 2
            ctx.beginPath()
            ctx.arc(root.size / 2, root.size / 2, r, 0, Math.PI * 1.4)
            ctx.stroke()
        }
        RotationAnimator on rotation {
            from: 0; to: 360
            duration: 900
            loops: Animation.Infinite
            running: root.running && root.visible
        }
    }
    onColorChanged: canvas.requestPaint()
}
