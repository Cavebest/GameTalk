import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// A keycap showing the bound key. Click it, then press a key (or Mouse 4/5) to rebind.
Item {
    id: kc
    property string current: ""
    property var allowed: []  // valid key names
    property bool allowNone: false
    signal picked(string key)
    property bool listening: false
    property string error: ""
    implicitWidth: Math.max(96, cap.implicitWidth)
    implicitHeight: 58

    function nameFor(event) {
        var k = event.key
        if (k >= Qt.Key_F1 && k <= Qt.Key_F24) return "F" + (k - Qt.Key_F1 + 1)
        var keypad = (event.modifiers & Qt.KeypadModifier) !== 0
        if (keypad) {
            if (k >= Qt.Key_0 && k <= Qt.Key_9) return "Numpad" + (k - Qt.Key_0)
            if (k === Qt.Key_Asterisk) return "NumpadMultiply"
            if (k === Qt.Key_Plus) return "NumpadAdd"
            if (k === Qt.Key_Minus) return "NumpadSubtract"
            if (k === Qt.Key_Period || k === Qt.Key_Comma) return "NumpadDecimal"
            if (k === Qt.Key_Slash) return "NumpadDivide"
        }
        var named = {}
        named[Qt.Key_Insert] = "Insert"; named[Qt.Key_Home] = "Home"; named[Qt.Key_End] = "End"
        named[Qt.Key_PageUp] = "PageUp"; named[Qt.Key_PageDown] = "PageDown"
        named[Qt.Key_Pause] = "Pause"; named[Qt.Key_ScrollLock] = "ScrollLock"
        return named[k] || ""
    }

    function accept(name) {
        if (name && allowed.indexOf(name) >= 0) {
            listening = false
            error = ""
            picked(name)
        } else {
            error = hub.t("That key can't be used — try F1–F24, Insert, Home, End, PageUp/Down, Numpad or Mouse 4/5.")
            shake.restart()
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
        acceptedButtons: Qt.LeftButton | Qt.BackButton | Qt.ForwardButton | Qt.RightButton
        onClicked: function(mouse) {
            if (kc.listening) {
                if (mouse.button === Qt.BackButton) kc.accept("Mouse4")
                else if (mouse.button === Qt.ForwardButton) kc.accept("Mouse5")
                else if (mouse.button === Qt.RightButton) kc.listening = false
                return
            }
            if (mouse.button === Qt.LeftButton) {
                kc.error = ""
                kc.listening = true
                catcher.forceActiveFocus()
            }
        }
    }

    Item {
        id: catcher
        focus: kc.listening
        Keys.onPressed: function(event) {
            event.accepted = true
            if (event.key === Qt.Key_Escape) { kc.listening = false; kc.error = ""; return }
            if ((event.key === Qt.Key_Delete || event.key === Qt.Key_Backspace) && kc.allowNone) {
                kc.listening = false
                kc.picked("")
                return
            }
            kc.accept(kc.nameFor(event))
        }
        onActiveFocusChanged: if (!activeFocus) kc.listening = false
    }
}
