import QtQuick
import QtQuick.Layouts

// Button with hover/press motion. kind: primary | ghost | danger | subtle
Rectangle {
    id: b
    property string text: ""
    property string icon: ""
    property string kind: "ghost"
    property bool small: false
    property bool busy: false
    signal clicked()

    readonly property bool hovered: mouse.containsMouse
    readonly property color fg: kind === "primary" ? "#ffffff"
                               : kind === "danger" ? Theme.danger
                               : hovered ? Theme.text : Theme.textSoft
    implicitHeight: small ? 32 : 40
    implicitWidth: row.implicitWidth + (small ? 24 : 32)
    radius: 8
    opacity: enabled ? 1 : 0.45
    color: kind === "primary" ? (mouse.pressed ? Theme.accentPress : hovered ? Theme.accentHover : Theme.accent)
         : kind === "danger" ? (hovered ? Theme.dangerSoftHover : Theme.dangerSoft)
         : kind === "subtle" ? (hovered ? Theme.raised : "transparent")
         : (hovered ? Theme.raised : Theme.surface2)
    border.width: kind === "subtle" || kind === "primary" ? 0 : 1
    border.color: kind === "danger" ? Theme.dangerBorder : hovered ? Theme.borderHover : Theme.border
    scale: mouse.pressed ? 0.97 : 1
    Behavior on color { ColorAnimation { duration: 140 } }
    Behavior on border.color { ColorAnimation { duration: 140 } }
    Behavior on scale { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
    Accessible.role: Accessible.Button
    Accessible.name: text

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Icon {
            visible: b.icon !== "" && !b.busy
            path: b.icon
            size: b.small ? 15 : 17
            color: b.fg
        }
        Spinner {
            visible: b.busy
            size: b.small ? 14 : 16
            color: b.fg
        }
        Text {
            visible: b.text !== ""
            text: b.text
            color: b.fg
            font.pixelSize: b.small ? 12 : 13
            font.weight: Font.DemiBold
            Behavior on color { ColorAnimation { duration: 140 } }
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: if (b.enabled && !b.busy) b.clicked()
    }
}
