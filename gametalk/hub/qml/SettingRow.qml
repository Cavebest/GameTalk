import QtQuick
import QtQuick.Layouts

// "Title + explanation" on one side, a control on the other.
RowLayout {
    id: row
    property string title: ""
    property string desc: ""
    property string icon: ""
    property string helpTopic: ""
    default property alias control: slot.data
    Layout.fillWidth: true
    spacing: 14

    Rectangle {
        visible: row.icon !== ""
        Layout.preferredWidth: 34
        Layout.preferredHeight: 34
        Layout.alignment: Qt.AlignTop
        radius: 9
        color: Theme.surface2
        Icon { anchors.centerIn: parent; path: row.icon; size: 17; color: Theme.textSoft }
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 3
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Text {
                text: row.title
                color: Theme.text
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
            HelpDot { visible: row.helpTopic !== ""; topic: row.helpTopic }
            Item { Layout.fillWidth: true }
        }
        Text {
            visible: row.desc !== ""
            text: row.desc
            color: Theme.muted
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }

    Item {
        id: slot
        Layout.alignment: Qt.AlignVCenter
        implicitWidth: childrenRect.width
        implicitHeight: childrenRect.height
    }
}
