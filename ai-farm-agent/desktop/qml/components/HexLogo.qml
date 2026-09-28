// Marca do app: hexagono desenhado (nao depende de fonte/glyph).
import QtQuick

Canvas {
    id: root
    property color tone: Theme.textPrimary
    property int sizePx: 16
    property real stroke: Math.max(1.5, sizePx / 9)

    implicitWidth: sizePx
    implicitHeight: sizePx
    onToneChanged: requestPaint()

    onPaint: {
        const ctx = getContext("2d")
        ctx.reset()
        const cx = width / 2, cy = height / 2
        const r = Math.min(width, height) / 2 - stroke
        ctx.lineWidth = stroke
        ctx.lineJoin = "round"
        ctx.strokeStyle = tone
        ctx.beginPath()
        for (let i = 0; i < 6; i++) {
            const a = Math.PI / 3 * i - Math.PI / 2
            const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a)
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
        }
        ctx.closePath()
        ctx.stroke()
    }
}
