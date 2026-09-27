import QtQuick
import QtQuick.Controls

// Multi-line text box (one item per line). `committed` fires when you leave it.
ScrollView {
    id: sv
    property alias text: ta.text
    property alias placeholderText: ta.placeholderText
    signal committed(string text)
    implicitHeight: 150
    clip: true
    background: Rectangle {
        radius: 8
        color: ta.activeFocus ? Theme.bg : Theme.surface2
        border.width: 1
        border.color: ta.activeFocus ? Theme.accent : Theme.border
        Behavior on border.color { ColorAnimation { duration: 150 } }
    }
    TextArea {
        id: ta
        color: Theme.text
        placeholderTextColor: Theme.faint
        selectionColor: Theme.accent
        selectedTextColor: "#ffffff"
        font.pixelSize: 13
        wrapMode: TextEdit.Wrap
        padding: 10
        background: null
        onActiveFocusChanged: if (!activeFocus) sv.committed(text)
    }
}
