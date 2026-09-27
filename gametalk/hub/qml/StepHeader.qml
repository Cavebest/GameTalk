import QtQuick
import QtQuick.Layouts

// "① Speech → text — who listens to your voice"
RowLayout {
    property string number: "1"
    property string title: ""
    property string hint: ""
    Layout.fillWidth: true
    Layout.topMargin: 6
    spacing: 10
    Rectangle {
        width: 26; height: 26; radius: 13
        color: Theme.accent
        Text { anchors.centerIn: parent; text: number; color: "#ffffff"; font.pixelSize: 13; font.weight: Font.Bold }
    }
    Text { text: title; color: Theme.text; font.pixelSize: 16; font.weight: Font.Bold }
    Text { text: "— " + hint; color: Theme.muted; font.pixelSize: 13 }
    Item { Layout.fillWidth: true }
}
