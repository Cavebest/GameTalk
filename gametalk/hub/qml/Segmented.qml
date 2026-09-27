import QtQuick
import QtQuick.Layouts

// Pill group with a highlight that slides to the chosen option.
Rectangle {
    id: seg
    property var items: []  // [{value, label}]
    property var current
    signal picked(var value)
    readonly property int index: {
        for (var i = 0; i < items.length; i++) if (items[i].value === current) return i
        return -1
    }
    implicitHeight: 38
    implicitWidth: row.implicitWidth + 8
    radius: 10
    color: Theme.surface2
    border.width: 1
    border.color: Theme.border
    opacity: enabled ? 1 : 0.45

    Rectangle {
        id: slider
        visible: seg.index >= 0
        // rep.count makes this re-evaluate once the Repeater has built its items
        property Item target: rep.count > 0 && seg.index >= 0 ? rep.itemAt(seg.index) : null
        x: target ? row.x + target.x : 4
        y: 4
        width: target ? target.width : 0
        height: seg.height - 8
        radius: 7
        color: Theme.accent
        Behavior on x { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
        Behavior on width { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
    }

    Row {
        id: row
        x: 4
        y: 4
        height: seg.height - 8
        Repeater {
            id: rep
            model: seg.items
            delegate: Item {
                required property var modelData
                required property int index
                width: lbl.implicitWidth + 28
                height: row.height
                Text {
                    id: lbl
                    anchors.centerIn: parent
                    text: modelData.label
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    color: seg.index === index ? "#ffffff" : (ma.containsMouse ? Theme.text : Theme.muted)
                    Behavior on color { ColorAnimation { duration: 160 } }
                }
                MouseArea {
                    id: ma
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: if (seg.enabled && seg.index !== index) seg.picked(modelData.value)
                }
            }
        }
    }
}
