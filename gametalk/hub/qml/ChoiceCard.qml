import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// A selectable option card (engines, recognisers…). The check badge pops in when chosen.
Rectangle {
    id: cc
    property string title: ""
    property string desc: ""
    property string icon: ""
    property var badges: []  // [{text, tone}] tone: ok | cloud | new
    property bool selected: false
    property string lockedNote: ""
    signal chosen()
    readonly property bool hovered: m.containsMouse
    implicitHeight: col.implicitHeight + 32
    radius: 12
    color: selected ? Theme.accentSoft : (hovered && enabled ? Theme.surface2 : Theme.surface)
    border.width: selected ? 2 : 1
    border.color: selected ? Theme.accent : (hovered && enabled ? Theme.borderHover : Theme.border)
    opacity: enabled ? 1 : 0.5
    scale: m.pressed && enabled ? 0.985 : 1
    Behavior on color { ColorAnimation { duration: 180 } }
    Behavior on border.color { ColorAnimation { duration: 180 } }
    Behavior on scale { NumberAnimation { duration: 120 } }

    ColumnLayout {
        id: col
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
        spacing: 8
        RowLayout {
            spacing: 10
            Layout.fillWidth: true
            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: 10
                color: cc.selected ? Theme.accent : Theme.surface2
                Behavior on color { ColorAnimation { duration: 180 } }
                Icon {
                    anchors.centerIn: parent
                    path: cc.icon
                    size: 19
                    color: cc.selected ? "#ffffff" : Theme.textSoft
                }
            }
            Text {
                text: cc.title
                color: Theme.text
                font.pixelSize: 14
                font.weight: Font.DemiBold
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Rectangle {  // check badge
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                radius: 11
                color: Theme.accent
                scale: cc.selected ? 1 : 0
                Behavior on scale { NumberAnimation { duration: 280; easing.type: Easing.OutBack; easing.overshoot: 2.2 } }
                Icon { anchors.centerIn: parent; path: Icons.check; size: 14; stroke: 2.4; color: "#ffffff" }
            }
        }
        Text {
            text: cc.enabled || cc.lockedNote === "" ? cc.desc : cc.lockedNote
            color: Theme.muted
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        Flow {
            Layout.fillWidth: true
            spacing: 6
            visible: cc.badges.length > 0
            Repeater {
                model: cc.badges
                delegate: Rectangle {
                    required property var modelData
                    height: 22
                    width: bt.implicitWidth + 16
                    radius: 11
                    color: modelData.tone === "ok" ? Theme.okSoft : modelData.tone === "new" ? Theme.accentSoft : Theme.surface2
                    border.width: 1
                    border.color: modelData.tone === "ok" ? Theme.okBorder : modelData.tone === "new" ? Theme.accent : Theme.border
                    Text {
                        id: bt
                        anchors.centerIn: parent
                        text: modelData.text
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        color: modelData.tone === "ok" ? Theme.ok : modelData.tone === "new" ? Theme.accent : Theme.textSoft
                    }
                }
            }
        }
    }

    MouseArea {
        id: m
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: cc.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (cc.enabled && !cc.selected) cc.chosen()
    }
    Accessible.role: Accessible.RadioButton
    Accessible.checked: selected
    Accessible.name: title
}
