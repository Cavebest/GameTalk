import QtQuick
import QtQuick.Controls

// Orange slider. `live` updates while dragging; `committed` fires once on release.
Slider {
    id: s
    signal committed(real value)
    property real bound: NaN  // the saved value; followed unless the user is dragging
    onBoundChanged: if (!pressed && !isNaN(bound)) value = bound
    Component.onCompleted: if (!isNaN(bound)) value = bound
    implicitHeight: 28
    implicitWidth: 220
    opacity: enabled ? 1 : 0.45
    onPressedChanged: if (!pressed) committed(value)

    background: Rectangle {
        x: s.leftPadding
        y: s.topPadding + s.availableHeight / 2 - height / 2
        width: s.availableWidth
        height: 4
        radius: 2
        color: Theme.track
        Rectangle {
            width: s.position * parent.width
            x: s.mirrored ? parent.width - width : 0
            height: parent.height
            radius: 2
            color: Theme.accent
        }
    }

    handle: Rectangle {
        x: s.leftPadding + s.visualPosition * (s.availableWidth - width)
        y: s.topPadding + s.availableHeight / 2 - height / 2
        width: 16
        height: 16
        radius: 8
        color: s.pressed ? Theme.accent : "#ffffff"
        border.width: 3
        border.color: Theme.accent
        scale: s.pressed ? 1.2 : (s.hovered ? 1.08 : 1)
        Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutBack } }
        Behavior on color { ColorAnimation { duration: 120 } }
    }
}
