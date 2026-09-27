import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// API key input. Once saved it collapses to a "saved" chip; the key itself never comes back.
RowLayout {
    id: sf
    property string title: ""
    property string path: ""
    property bool saved: false
    property string placeholder: hub.t("paste key here")
    Layout.fillWidth: true
    spacing: 10

    Text {
        text: sf.title
        color: Theme.textSoft
        font.pixelSize: 13
        Layout.preferredWidth: 150
        elide: Text.ElideRight
    }
    Rectangle {
        visible: sf.saved
        Layout.fillWidth: true
        implicitHeight: 38
        radius: 8
        color: Theme.okSoft
        border.width: 1
        border.color: Theme.okBorder
        RowLayout {
            anchors { fill: parent; leftMargin: 12; rightMargin: 6 }
            Icon { path: Icons.lock; size: 15; color: Theme.ok }
            Text { text: hub.t("Saved and encrypted"); color: Theme.ok; font.pixelSize: 12; font.weight: Font.DemiBold; Layout.fillWidth: true }
            Btn { text: hub.t("Remove"); small: true; kind: "subtle"; icon: Icons.trash; onClicked: hub.clearSecret(sf.path) }
        }
    }
    Field {
        id: input
        visible: !sf.saved
        Layout.fillWidth: true
        echoMode: TextInput.Password
        placeholderText: sf.placeholder
        onAccepted: if (text.trim()) { hub.setSecret(sf.path, text); text = "" }
    }
    Btn {
        visible: !sf.saved
        text: hub.t("Save")
        kind: "primary"
        small: true
        enabled: input.text.trim().length > 0
        onClicked: { hub.setSecret(sf.path, input.text); input.text = "" }
    }
}
