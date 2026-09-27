import QtQuick
import "icons.js" as Icons

// Row of colour dots; the chosen one gets a ring and a check.
Flow {
    id: sw
    property var colors: []
    property string current: ""
    signal picked(string color)
    spacing: 8
    Repeater {
        model: sw.colors
        delegate: Rectangle {
            id: dot
            required property string modelData
            readonly property bool chosen: sw.current.toLowerCase() === modelData.toLowerCase()
            readonly property color c: modelData
            readonly property bool light: c.r * 0.299 + c.g * 0.587 + c.b * 0.114 > 0.62
            width: 26; height: 26; radius: 13
            color: "transparent"
            border.width: 2
            border.color: chosen ? Theme.text : (dm.containsMouse ? Theme.borderHover : "transparent")
            Behavior on border.color { ColorAnimation { duration: 140 } }
            Rectangle {
                anchors.centerIn: parent
                width: 18; height: 18; radius: 9
                color: dot.modelData
                border.width: 1  // keeps the near-black choices visible on the dark card
                border.color: Theme.borderHover
                scale: dm.pressed ? 0.85 : 1
                Behavior on scale { NumberAnimation { duration: 120 } }
                Icon {
                    anchors.centerIn: parent
                    visible: dot.chosen
                    path: Icons.check
                    size: 12
                    stroke: 2.6
                    color: dot.light ? "#111111" : "#ffffff"
                }
            }
            MouseArea {
                id: dm
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: sw.picked(dot.modelData)
            }
        }
    }
}
