import QtQuick

// The GameTalk mark: an orange speech bubble with "EN".
Item {
    id: logo
    property real size: 28
    implicitWidth: size
    implicitHeight: size
    Rectangle {
        width: logo.size
        height: logo.size * 0.8
        radius: logo.size * 0.2
        color: Theme.accent
        Text {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -1
            text: "EN"
            color: "#ffffff"
            font.pixelSize: logo.size * 0.34
            font.weight: Font.Black
            font.letterSpacing: 0.5
        }
    }
    Rectangle {  // bubble tail
        x: logo.size * 0.2
        y: logo.size * 0.68
        width: logo.size * 0.22
        height: width
        rotation: 45
        color: Theme.accent
        z: -1
    }
}
