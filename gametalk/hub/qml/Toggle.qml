import QtQuick

// Animated on/off switch. The knob springs across and stretches while pressed.
Item {
    id: t
    property bool checked: false
    signal toggled(bool on)
    readonly property bool mirror: LayoutMirroring.enabled
    implicitWidth: 44
    implicitHeight: 24
    opacity: enabled ? 1 : 0.4
    Accessible.role: Accessible.CheckBox
    Accessible.checked: checked

    Rectangle {
        id: track
        anchors.fill: parent
        radius: height / 2
        color: t.checked ? Theme.accent : (mouse.containsMouse ? Theme.trackHover : Theme.track)
        Behavior on color { ColorAnimation { duration: 180 } }

        Rectangle {
            id: knob
            readonly property bool onRight: t.checked !== t.mirror
            width: mouse.pressed ? 23 : 18
            height: 18
            radius: 9
            y: 3
            x: onRight ? track.width - width - 3 : 3
            color: t.checked ? "#ffffff" : Theme.knob
            Behavior on x { NumberAnimation { duration: 260; easing.type: Easing.OutBack; easing.overshoot: 1.6 } }
            Behavior on width { NumberAnimation { duration: 120 } }
            Behavior on color { ColorAnimation { duration: 180 } }
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        anchors.margins: -4
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: if (t.enabled) t.toggled(!t.checked)
    }
}
