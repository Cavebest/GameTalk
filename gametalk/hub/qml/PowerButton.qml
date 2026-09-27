import QtQuick
import QtQuick.Shapes
import "icons.js" as Icons

// Big round start/stop button. Breathes while running, spins while starting,
// and sends out ripples while you talk.
Item {
    id: pb
    property bool running: false
    property bool busy: false
    property bool live: false
    signal clicked()
    implicitWidth: 84
    implicitHeight: 84

    Repeater {  // ripples while the mic is open
        model: 2
        delegate: Rectangle {
            id: ripple
            required property int index
            anchors.centerIn: parent
            width: pb.width
            height: pb.height
            radius: width / 2
            color: "transparent"
            border.width: 2
            border.color: Theme.danger
            opacity: 0
            SequentialAnimation on scale {
                running: pb.live
                loops: Animation.Infinite
                PauseAnimation { duration: index * 450 }
                NumberAnimation { from: 1; to: 1.55; duration: 900; easing.type: Easing.OutCubic }
            }
            SequentialAnimation on opacity {
                running: pb.live
                loops: Animation.Infinite
                PauseAnimation { duration: index * 450 }
                NumberAnimation { from: 0.7; to: 0; duration: 900 }
                onStopped: ripple.opacity = 0
            }
        }
    }

    Rectangle {  // soft halo that breathes while running
        anchors.centerIn: parent
        width: pb.width + 14
        height: width
        radius: width / 2
        color: "transparent"
        border.width: 3
        border.color: pb.running ? Theme.ok : Theme.accent
        opacity: pb.running ? 0.35 : 0.0
        Behavior on opacity { NumberAnimation { duration: 300 } }
        SequentialAnimation on scale {
            running: pb.running && !pb.live
            loops: Animation.Infinite
            NumberAnimation { to: 1.06; duration: 1400; easing.type: Easing.InOutSine }
            NumberAnimation { to: 1.0; duration: 1400; easing.type: Easing.InOutSine }
        }
    }

    Rectangle {
        id: face
        anchors.fill: parent
        radius: width / 2
        color: pb.running ? (m.containsMouse ? Theme.dangerSoftHover : Theme.surface2)
                          : (m.pressed ? Theme.accentPress : m.containsMouse ? Theme.accentHover : Theme.accent)
        border.width: pb.running ? 2 : 0
        border.color: m.containsMouse ? Theme.danger : Theme.borderHover
        scale: m.pressed ? 0.94 : (m.containsMouse ? 1.04 : 1)
        Behavior on color { ColorAnimation { duration: 220 } }
        Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }

        Icon {
            anchors.centerIn: parent
            visible: !pb.busy
            path: pb.running ? (m.containsMouse ? Icons.stop : Icons.power) : Icons.power
            size: 34
            stroke: 2.4
            color: pb.running ? (m.containsMouse ? Theme.danger : Theme.ok) : "#ffffff"
        }
        Spinner {
            anchors.centerIn: parent
            visible: pb.busy
            size: 36
            line: 3
            color: pb.running ? Theme.accent : "#ffffff"
        }
    }

    MouseArea {
        id: m
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: pb.clicked()
    }
    Accessible.role: Accessible.Button
    Accessible.name: running ? hub.t("Stop GameTalk") : hub.t("Start GameTalk")
}
