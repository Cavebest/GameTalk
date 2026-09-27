import QtQuick
import QtQuick.Layouts

// Voice → engine → translator → screen. A spark runs along the path on every translation.
Item {
    id: pl
    property var nodes: []
    property real pulseKey: 0
    readonly property bool mirror: LayoutMirroring.enabled
    implicitHeight: 112
    readonly property real nodeW: Math.min(170, (width - 3 * 28) / 4)
    readonly property real stepX: (width - nodeW) / 3

    function nodeX(i) { return mirror ? width - nodeW - i * stepX : i * stepX }

    Rectangle {  // the track
        x: nodeW / 2
        width: pl.width - nodeW
        y: 30
        height: 2
        color: Theme.border
    }

    Rectangle {  // the spark
        id: spark
        width: 44
        height: 4
        radius: 2
        y: 29
        opacity: 0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "transparent" }
            GradientStop { position: pl.mirror ? 0.2 : 0.8; color: Theme.accent }
            GradientStop { position: 1; color: pl.mirror ? "transparent" : "#ffd2bf" }
        }
    }
    SequentialAnimation {
        id: run
        PropertyAction { target: spark; property: "opacity"; value: 1 }
        NumberAnimation {
            target: spark
            property: "x"
            from: pl.mirror ? pl.width - pl.nodeW / 2 : pl.nodeW / 2 - spark.width
            to: pl.mirror ? pl.nodeW / 2 - spark.width : pl.width - pl.nodeW / 2
            duration: 1100
            easing.type: Easing.InOutCubic
        }
        NumberAnimation { target: spark; property: "opacity"; to: 0; duration: 250 }
    }
    onPulseKeyChanged: if (pulseKey) { run.restart(); flash.restart() }

    Repeater {
        model: pl.nodes
        delegate: Item {
            id: node
            required property var modelData
            required property int index
            x: pl.nodeX(index)
            width: pl.nodeW
            height: pl.height
            Rectangle {
                id: bubble
                anchors.horizontalCenter: parent.horizontalCenter
                width: 60
                height: 60
                radius: 16
                color: Theme.surface2
                border.width: 1
                border.color: Theme.borderHover
                Icon { anchors.centerIn: parent; path: node.modelData.icon; size: 26; color: Theme.text }
                SequentialAnimation on border.color {
                    id: glow
                    running: false
                    PauseAnimation { duration: node.index * 300 }
                    ColorAnimation { to: Theme.accent; duration: 120 }
                    ColorAnimation { to: Theme.borderHover; duration: 700 }
                }
                Connections {
                    target: flash
                    function onStarted() { glow.restart() }
                }
            }
            Text {
                anchors.top: bubble.bottom
                anchors.topMargin: 8
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                text: node.modelData.title
                color: Theme.text
                font.pixelSize: 12
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Text {
                anchors.top: bubble.bottom
                anchors.topMargin: 27
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                text: node.modelData.sub
                color: Theme.muted
                font.pixelSize: 11
                elide: Text.ElideRight
            }
        }
    }
    PauseAnimation { id: flash; duration: 1 }
}
