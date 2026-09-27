import QtQuick
import QtQuick.Shapes

// Circular gauge that sweeps to its value (0..1).
Item {
    id: r
    property real value: 0
    property color color: value >= 1 ? Theme.danger : value >= 0.8 ? Theme.warn : Theme.accent
    property real size: 76
    property real line: 7
    property string caption: ""
    property real shown: 0
    implicitWidth: size
    implicitHeight: size
    Behavior on shown { NumberAnimation { duration: 1100; easing.type: Easing.OutCubic } }
    Component.onCompleted: shown = Qt.binding(function() { return Math.min(1, value) })

    Shape {
        anchors.fill: parent
        antialiasing: true
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: Theme.track
            strokeWidth: r.line
            fillColor: "transparent"
            PathAngleArc {
                centerX: r.size / 2; centerY: r.size / 2
                radiusX: r.size / 2 - r.line / 2; radiusY: r.size / 2 - r.line / 2
                startAngle: 0; sweepAngle: 360
            }
        }
        ShapePath {
            strokeColor: r.color
            strokeWidth: r.line
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                centerX: r.size / 2; centerY: r.size / 2
                radiusX: r.size / 2 - r.line / 2; radiusY: r.size / 2 - r.line / 2
                startAngle: -90; sweepAngle: Math.max(0.01, 360 * r.shown)
            }
        }
    }

    Column {
        anchors.centerIn: parent
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: (r.value > 0 && r.value < 0.01 ? "<1" : Math.round(r.shown * 100)) + "%"
            color: Theme.text
            font.pixelSize: r.size * 0.22
            font.weight: Font.DemiBold
        }
    }
}
