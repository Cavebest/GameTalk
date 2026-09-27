import QtQuick
import QtQuick.Shapes

// Rotating arc for "working…" states.
Item {
    id: s
    property real size: 18
    property color color: Theme.accent
    property real line: 2
    implicitWidth: size
    implicitHeight: size

    Shape {
        anchors.fill: parent
        antialiasing: true
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: s.color
            strokeWidth: s.line
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                centerX: s.size / 2
                centerY: s.size / 2
                radiusX: s.size / 2 - s.line
                radiusY: s.size / 2 - s.line
                startAngle: 0
                sweepAngle: 250
            }
        }
        RotationAnimation on rotation {
            running: s.visible
            from: 0
            to: 360
            duration: 900
            loops: Animation.Infinite
        }
    }
}
