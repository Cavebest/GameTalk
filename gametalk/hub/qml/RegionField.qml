import QtQuick
import QtQuick.Layouts

// Plain text setting that saves when you press Enter or leave the field.
RowLayout {
    id: rf
    property string title: ""
    property string path: ""
    property string value: ""
    property string hint: ""
    Layout.fillWidth: true
    spacing: 10
    Text { text: rf.title; color: Theme.textSoft; font.pixelSize: 13; Layout.preferredWidth: 150; elide: Text.ElideRight }
    Field {
        id: input
        Layout.fillWidth: true
        text: rf.value
        placeholderText: rf.hint
        onEditingFinished: if (text !== rf.value) hub.set(rf.path, text)
    }
}
