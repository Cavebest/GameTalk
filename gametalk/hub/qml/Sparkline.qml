import QtQuick

// Tiny line chart of recent response times; draws itself in from left to right.
Canvas {
    id: c
    property var points: []
    property color color: Theme.accent
    property real reveal: 1
    implicitHeight: 34
    onPointsChanged: { reveal = 0; anim.restart() }
    onRevealChanged: requestPaint()
    onWidthChanged: requestPaint()

    NumberAnimation { id: anim; target: c; property: "reveal"; from: 0; to: 1; duration: 700; easing.type: Easing.OutCubic }

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        var p = points || []
        if (p.length < 2) {
            ctx.strokeStyle = Theme.track
            ctx.lineWidth = 2
            ctx.setLineDash([3, 4])
            ctx.beginPath(); ctx.moveTo(0, height / 2); ctx.lineTo(width, height / 2); ctx.stroke()
            return
        }
        var max = Math.max.apply(null, p) * 1.15, min = Math.min.apply(null, p) * 0.85
        var span = Math.max(0.001, max - min)
        var step = width / (p.length - 1)
        ctx.save()
        ctx.beginPath(); ctx.rect(0, 0, width * reveal, height); ctx.clip()
        var grad = ctx.createLinearGradient(0, 0, 0, height)
        grad.addColorStop(0, Qt.rgba(c.color.r, c.color.g, c.color.b, 0.28))
        grad.addColorStop(1, Qt.rgba(c.color.r, c.color.g, c.color.b, 0))
        ctx.beginPath()
        for (var i = 0; i < p.length; i++) {
            var x = i * step, y = height - 3 - (p[i] - min) / span * (height - 6)
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
        }
        ctx.lineWidth = 2
        ctx.strokeStyle = c.color
        ctx.lineJoin = "round"
        ctx.stroke()
        ctx.lineTo(width, height); ctx.lineTo(0, height); ctx.closePath()
        ctx.fillStyle = grad
        ctx.fill()
        ctx.restore()
    }
}
