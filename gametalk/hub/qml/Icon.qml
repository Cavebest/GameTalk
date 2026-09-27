import QtQuick
import QtQuick.Shapes

// A crisp stroke icon from icons.js; its colour animates when changed.
Item {
    id: root
    property string path: ""
    property color color: Theme.text
    property real size: 20
    property real stroke: 1.8
    implicitWidth: size
    implicitHeight: size
    Behavior on color { ColorAnimation { duration: 160 } }

    Shape {
        width: 24
        height: 24
        scale: root.size / 24
        transformOrigin: Item.TopLeft
        antialiasing: true
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: root.color
            strokeWidth: root.stroke
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: root.path }
        }
    }
}
