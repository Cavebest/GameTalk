import QtQuick

// Little "?" that opens the built-in help on a topic.
Rectangle {
    id: d
    property string topic: "start"
    width: 18
    height: 18
    radius: 9
    color: m.containsMouse ? Theme.accentSoft : Theme.surface2
    border.width: 1
    border.color: m.containsMouse ? Theme.accent : Theme.border
    Behavior on color { ColorAnimation { duration: 140 } }
    Text {
        anchors.centerIn: parent
        text: "?"
        color: m.containsMouse ? Theme.accent : Theme.muted
        font.pixelSize: 11
        font.weight: Font.Bold
    }
    MouseArea {
        id: m
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: hub.openHelp(d.topic)
    }
    Accessible.role: Accessible.Button
    Accessible.name: hub.t("Help")
}
