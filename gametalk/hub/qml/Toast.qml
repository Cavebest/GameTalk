import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// Small notice that slides up from the bottom and fades away.
Rectangle {
    id: toast
    property string kind: "ok"
    property bool shown: false
    function show(message, k) {
        msg.text = message
        kind = k || "ok"
        shown = true
        hideTimer.restart()
    }
    anchors.horizontalCenter: parent.horizontalCenter
    y: parent.height - (shown ? height + 26 : -10)
    opacity: shown ? 1 : 0
    width: row.implicitWidth + 36
    height: 44
    radius: 12
    color: Theme.raised
    border.width: 1
    border.color: kind === "error" ? Theme.dangerBorder : kind === "warn" ? Theme.warnBorder : Theme.okBorder
    z: 100
    Behavior on y { NumberAnimation { duration: 320; easing.type: Easing.OutBack; easing.overshoot: 1.2 } }
    Behavior on opacity { NumberAnimation { duration: 220 } }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 10
        Icon {
            path: toast.kind === "error" ? Icons.close : toast.kind === "warn" ? Icons.help : Icons.check
            size: 16
            stroke: 2.2
            color: toast.kind === "error" ? Theme.danger : toast.kind === "warn" ? Theme.warn : Theme.ok
        }
        Text { id: msg; color: Theme.text; font.pixelSize: 13; font.weight: Font.DemiBold }
    }
    Timer { id: hideTimer; interval: 2600; onTriggered: toast.shown = false }
}
