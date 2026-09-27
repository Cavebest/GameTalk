import QtQuick
import QtQuick.Controls

// Styled text input.
TextField {
    id: f
    implicitHeight: 38
    implicitWidth: 240
    color: Theme.text
    placeholderTextColor: Theme.faint
    selectionColor: Theme.accent
    selectedTextColor: "#ffffff"
    font.pixelSize: 13
    leftPadding: 12
    rightPadding: 12
    horizontalAlignment: Text.AlignLeft
    opacity: enabled ? 1 : 0.45
    background: Rectangle {
        radius: 8
        color: f.activeFocus ? Theme.bg : Theme.surface2
        border.width: 1
        border.color: f.activeFocus ? Theme.accent : (f.hovered ? Theme.borderHover : Theme.border)
        Behavior on border.color { ColorAnimation { duration: 150 } }
        Behavior on color { ColorAnimation { duration: 150 } }
    }
}
