import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Scrollable page body with a title/subtitle header.
Flickable {
    id: f
    property string title: ""
    property string subtitle: ""
    property string helpTopic: ""
    default property alias content: col.data
    signal navigate(int page)
    contentWidth: width
    contentHeight: col.implicitHeight + head.height + 60
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    flickDeceleration: 4000
    maximumFlickVelocity: 3500

    ColumnLayout {
        id: head
        x: 32
        y: 26
        width: f.width - 64
        spacing: 4
        RowLayout {
            spacing: 10
            Text {
                text: f.title
                color: Theme.text
                font.pixelSize: 24
                font.weight: Font.Bold
            }
            HelpDot { visible: f.helpTopic !== ""; topic: f.helpTopic }
        }
        Text {
            visible: f.subtitle !== ""
            text: f.subtitle
            color: Theme.muted
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }

    ColumnLayout {
        id: col
        x: 32
        y: head.y + head.height + 22
        width: f.width - 64
        spacing: 16
    }

    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AsNeeded
        contentItem: Rectangle {
            implicitWidth: 6
            radius: 3
            color: parent.pressed ? Theme.borderHover : Theme.border
        }
    }
}
