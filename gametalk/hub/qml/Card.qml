import QtQuick
import QtQuick.Layouts

// Dark panel with a hairline border that lights up on hover.
Rectangle {
    id: card
    default property alias content: inner.data
    property real padding: 18
    property bool accentEdge: false
    property bool hoverable: true
    property alias spacing: inner.spacing
    readonly property bool hovered: hover.hovered
    implicitHeight: inner.implicitHeight + padding * 2
    radius: 12
    color: Theme.surface
    border.width: 1
    border.color: hoverable && hovered ? Theme.borderHover : Theme.border
    Behavior on border.color { ColorAnimation { duration: 180 } }

    HoverHandler { id: hover }

    Rectangle {  // orange edge, GG-style, on the reading-start side
        visible: card.accentEdge
        width: 3
        radius: 2
        color: Theme.accent
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom; margins: 10 }
    }

    ColumnLayout {
        id: inner
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: card.padding }
        spacing: 12
    }
}
