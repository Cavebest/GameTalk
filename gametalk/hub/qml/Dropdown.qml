import QtQuick
import QtQuick.Controls
import "icons.js" as Icons

// Styled picker. items: [{value, label, note}], current: the selected value.
ComboBox {
    id: c
    property var items: []
    property var current
    signal picked(var value)
    model: items
    textRole: "label"
    valueRole: "value"
    implicitHeight: 38
    implicitWidth: 220
    font.pixelSize: 13
    opacity: enabled ? 1 : 0.45

    function sync() { currentIndex = indexOfValue(current) }
    onCurrentChanged: sync()
    onItemsChanged: sync()
    Component.onCompleted: sync()
    onActivated: picked(currentValue)

    background: Rectangle {
        radius: 8
        color: c.hovered ? Theme.raised : Theme.surface2
        border.width: 1
        border.color: c.popup.visible || c.activeFocus ? Theme.accent : (c.hovered ? Theme.borderHover : Theme.border)
        Behavior on border.color { ColorAnimation { duration: 150 } }
        Behavior on color { ColorAnimation { duration: 150 } }
    }

    contentItem: Text {
        leftPadding: c.mirrored ? 34 : 12
        rightPadding: c.mirrored ? 12 : 34
        text: c.displayText
        color: Theme.text
        font: c.font
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignLeft
        elide: Text.ElideRight
    }

    indicator: Icon {
        x: c.mirrored ? 11 : c.width - width - 11
        y: (c.height - height) / 2
        path: Icons.chevronDown
        size: 15
        color: c.popup.visible ? Theme.accent : Theme.muted
        rotation: c.popup.visible ? 180 : 0
        Behavior on rotation { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
    }

    delegate: ItemDelegate {
        id: d
        required property var modelData
        required property int index
        width: ListView.view ? ListView.view.width : c.width
        height: modelData.note ? 44 : 34
        highlighted: c.highlightedIndex === index
        contentItem: Column {
            spacing: 1
            Text {
                text: d.modelData.label
                color: c.currentIndex === d.index ? Theme.accent : Theme.text
                font.pixelSize: 13
                font.weight: c.currentIndex === d.index ? Font.DemiBold : Font.Normal
                width: parent.width
                horizontalAlignment: Text.AlignLeft
                elide: Text.ElideRight
            }
            Text {
                visible: !!d.modelData.note
                text: d.modelData.note || ""
                color: Theme.muted
                font.pixelSize: 11
                width: parent.width
                horizontalAlignment: Text.AlignLeft
            }
        }
        background: Rectangle {
            radius: 6
            color: d.highlighted ? Theme.raised : "transparent"
            Behavior on color { ColorAnimation { duration: 100 } }
        }
    }

    popup: Popup {
        y: c.height + 4
        width: c.width
        implicitHeight: Math.min(list.contentHeight + 10, 340)
        padding: 5
        contentItem: ListView {
            id: list
            clip: true
            model: c.popup.visible ? c.delegateModel : null
            currentIndex: c.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
            ScrollIndicator.vertical: ScrollIndicator {}
        }
        background: Rectangle {
            radius: 10
            color: Theme.surface2
            border.width: 1
            border.color: Theme.borderHover
        }
        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 140 }
            NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 180; easing.type: Easing.OutCubic }
        }
        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 100 }
        }
    }
}
