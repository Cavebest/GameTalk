import QtQuick
import QtQuick.Controls

// Dark tooltip that fades in (the default one is a white box).
ToolTip {
    id: tip
    delay: 500
    padding: 8
    contentItem: Text {
        text: tip.text
        color: Theme.text
        font.pixelSize: 12
    }
    background: Rectangle {
        radius: 7
        color: Theme.raised
        border.width: 1
        border.color: Theme.borderHover
    }
    enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 140 } }
    exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 100 } }
}
