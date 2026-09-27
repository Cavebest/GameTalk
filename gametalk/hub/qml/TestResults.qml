import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// ✓ / ✗ lines from a connection test, sliding in one after another.
ColumnLayout {
    id: tr
    property var lines: []
    Layout.fillWidth: true
    spacing: 6
    visible: lines.length > 0
    Repeater {
        model: tr.lines
        delegate: Rectangle {
            id: line
            required property var modelData
            required property int index
            Layout.fillWidth: true
            implicitHeight: lt.implicitHeight + 16
            radius: 8
            color: modelData.ok ? Theme.okSoft : Theme.dangerSoft
            border.width: 1
            border.color: modelData.ok ? Theme.okBorder : Theme.dangerBorder
            opacity: 0
            Component.onCompleted: fade.start()
            NumberAnimation { id: fade; target: line; property: "opacity"; to: 1; duration: 260 + line.index * 120 }
            RowLayout {
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 10 }
                spacing: 8
                Icon { path: line.modelData.ok ? Icons.check : Icons.close; size: 15; stroke: 2.4; color: line.modelData.ok ? Theme.ok : Theme.danger }
                Text { id: lt; text: line.modelData.text; color: Theme.text; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
        }
    }
}
