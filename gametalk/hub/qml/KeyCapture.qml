import QtQuick
import "icons.js" as Icons

// A keycap showing the bound key. Click it, then press any key or Mouse 4/5 to rebind
// (Esc cancels). The key is caught by GameTalk's own hotkey system, exactly as in a game.
Item {
    id: kc
    property string target: ""   // which binding this is (talk, replay, quicktext…)
    property string current: ""
    property var allowed: []
    signal picked(string key)
    property bool listening: false
    property string error: ""
    implicitWidth: Math.max(96, cap.implicitWidth)
    implicitHeight: 58

    function accept(name) {
        if (allowed.length && allowed.indexOf(name) < 0) {
            error = hub.t("That key can't be used — try F1–F24, Insert, Home, End, PageUp/Down, Numpad or Mouse 4/5.")
            shake.restart()
            return
        }
        error = ""
        picked(name)
    }
    function stop() {
        if (listening) { listening = false; hub.cancelCapture() }
    }
    Component.onDestruction: stop()
    onEnabledChanged: if (!enabled) stop()

    Connections {
        target: hub
        function onKeyCaptured(who, name) {
            if (who !== kc.target) return
            kc.listening = false
            if (name) kc.accept(name)
        }
    }

    Rectangle {  // the keycap: a lighter top face over a darker base
        id: cap
        implicitWidth: label.implicitWidth + 40
        width: parent.width
        height: 54
        radius: 10
        color: kc.listening ? Theme.accentPress : Theme.keyBase
        Behavior on color { ColorAnimation { duration: 180 } }
        Rectangle {
            id: face
            x: 3
            y: area.pressed ? 4 : 2
            width: parent.width - 6
            height: parent.height - 9
            radius: 8
            color: kc.listening ? Theme.accent : (area.containsMouse ? Theme.keyHover : Theme.keyFace)
            border.width: 1
            border.color: kc.listening ? Theme.accentHover : Theme.borderHover
            Behavior on y { NumberAnimation { duration: 80 } }
            Behavior on color { ColorAnimation { duration: 160 } }
            Text {
                id: label
                anchors.centerIn: parent
                text: kc.listening ? hub.t("Press a key…") : (kc.current || hub.t("None"))
                color: kc.listening ? "#ffffff" : Theme.text
                font.pixelSize: kc.listening ? 13 : 17
                font.weight: Font.Bold
                font.family: kc.listening ? Theme.font : Theme.mono
            }
            SequentialAnimation on opacity {
                running: kc.listening
                loops: Animation.Infinite
                NumberAnimation { to: 0.75; duration: 520 }
                NumberAnimation { to: 1; duration: 520 }
                onStopped: face.opacity = 1
            }
        }
        transform: Translate { id: shakeX; x: 0 }
    }

    SequentialAnimation {
        id: shake
        NumberAnimation { target: shakeX; property: "x"; to: -6; duration: 50 }
        NumberAnimation { target: shakeX; property: "x"; to: 6; duration: 60 }
        NumberAnimation { target: shakeX; property: "x"; to: -3; duration: 50 }
        NumberAnimation { target: shakeX; property: "x"; to: 0; duration: 50 }
    }

    MouseArea {
        id: area
        anchors.fill: cap
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: function(mouse) {
            if (kc.listening) { kc.stop(); return }  // a second click (or right-click) cancels
            if (mouse.button !== Qt.LeftButton) return
            kc.error = ""
            kc.listening = true
            hub.beginCapture(kc.target)
        }
    }
}
