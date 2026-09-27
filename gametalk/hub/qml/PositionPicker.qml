import QtQuick

// 3x3 screen map: click where the text should appear. Never mirrored (it's the screen).
Rectangle {
    id: pp
    property string current: "top-center"
    signal picked(string value)
    readonly property var cells: ["top-left", "top-center", "top-right",
                                  "middle-left", "center", "middle-right",
                                  "bottom-left", "bottom-center", "bottom-right"]
    readonly property int index: Math.max(0, cells.indexOf(current))
    LayoutMirroring.enabled: false
    LayoutMirroring.childrenInherit: true
    implicitWidth: 150
    implicitHeight: 96
    radius: 10
    color: Theme.bg
    border.width: 1
    border.color: Theme.border

    readonly property real cw: (width - 16) / 3
    readonly property real ch: (height - 16) / 3

    Rectangle {  // moving highlight
        x: 8 + (pp.index % 3) * pp.cw + 2
        y: 8 + Math.floor(pp.index / 3) * pp.ch + 2
        width: pp.cw - 4
        height: pp.ch - 4
        radius: 6
        color: Theme.accentSoft
        border.width: 1
        border.color: Theme.accent
        Behavior on x { NumberAnimation { duration: 260; easing.type: Easing.OutBack } }
        Behavior on y { NumberAnimation { duration: 260; easing.type: Easing.OutBack } }
    }

    Repeater {
        model: 9
        delegate: Item {
            required property int index
            x: 8 + (index % 3) * pp.cw
            y: 8 + Math.floor(index / 3) * pp.ch
            width: pp.cw
            height: pp.ch
            Rectangle {
                anchors.centerIn: parent
                width: pp.index === index ? 18 : (cm.containsMouse ? 12 : 8)
                height: pp.index === index ? 5 : (cm.containsMouse ? 5 : 4)
                radius: 2.5
                color: pp.index === index ? Theme.accent : (cm.containsMouse ? Theme.textSoft : Theme.faint)
                Behavior on width { NumberAnimation { duration: 160 } }
                Behavior on color { ColorAnimation { duration: 160 } }
            }
            MouseArea {
                id: cm
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: pp.picked(pp.cells[index])
            }
        }
    }
}
