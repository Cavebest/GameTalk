import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Profiles")
    subtitle: hub.t("Each game can have its own key, engines, overlay, phrases and corrections. Add the game's .exe and it switches by itself.")
    helpTopic: "profiles"

    readonly property var cfg: hub.config
    property bool confirmDelete: false
    Timer { id: unconfirm; interval: 3000; onTriggered: page.confirmDelete = false }

    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 1000 ? 3 : 2
        columnSpacing: 14
        rowSpacing: 14
        Repeater {
            model: page.cfg.profiles
            delegate: Rectangle {
                id: pc
                required property string modelData
                required property int index
                readonly property bool active: modelData === page.cfg.active_profile
                Layout.fillWidth: true
                implicitHeight: 86
                radius: 12
                color: active ? Theme.accentSoft : (pm.containsMouse ? Theme.surface2 : Theme.surface)
                border.width: active ? 2 : 1
                border.color: active ? Theme.accent : (pm.containsMouse ? Theme.borderHover : Theme.border)
                scale: pm.pressed ? 0.98 : 1
                opacity: 0
                Component.onCompleted: pop.start()
                NumberAnimation { id: pop; target: pc; property: "opacity"; to: 1; duration: 240 + pc.index * 40 }
                Behavior on color { ColorAnimation { duration: 180 } }
                Behavior on scale { NumberAnimation { duration: 120 } }
                RowLayout {
                    anchors { fill: parent; margins: 16 }
                    spacing: 12
                    Rectangle {
                        width: 44; height: 44; radius: 12
                        color: pc.active ? Theme.accent : Theme.surface2
                        Text {
                            anchors.centerIn: parent
                            text: pc.modelData.substring(0, 2).toUpperCase()
                            color: pc.active ? "#ffffff" : Theme.textSoft
                            font.pixelSize: 15
                            font.weight: Font.Bold
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text { text: pc.modelData; color: Theme.text; font.pixelSize: 14; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                        Text {
                            text: pc.active ? hub.t("Active now") : hub.t("Click to use")
                            color: pc.active ? Theme.accent : Theme.muted
                            font.pixelSize: 11
                        }
                    }
                }
                MouseArea { id: pm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: if (!pc.active) hub.setProfile(pc.modelData) }
            }
        }
    }

    Card {
        Layout.fillWidth: true
        padding: 20
        Caption { text: hub.tf("Profile: {name}", {name: page.cfg.active_profile}) }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Field { id: nameField; Layout.fillWidth: true; placeholderText: hub.t("Name, e.g. CS2 or Valorant") }
            Btn { text: hub.t("New"); icon: Icons.plus; small: true; onClicked: { hub.newProfile(nameField.text); nameField.text = "" } }
            Btn { text: hub.t("Rename"); icon: Icons.pencil; small: true; enabled: nameField.text.trim() !== ""; onClicked: { hub.renameProfile(nameField.text); nameField.text = "" } }
        }
        Text {
            text: hub.t("New copies the current profile. Type a name first; Rename uses the same box.")
            color: Theme.faint
            font.pixelSize: 11
        }
        Flow {
            Layout.fillWidth: true
            spacing: 8
            Btn { text: hub.t("Export…"); icon: Icons.upload; small: true; onClicked: hub.exportProfile() }
            Btn { text: hub.t("Import…"); icon: Icons.download; small: true; onClicked: hub.importProfile() }
            Btn {
                text: page.confirmDelete ? hub.t("Click again to delete") : hub.t("Delete")
                icon: Icons.trash
                small: true
                kind: "danger"
                enabled: page.cfg.profiles.length > 1
                onClicked: {
                    if (page.confirmDelete) { page.confirmDelete = false; hub.deleteProfile() }
                    else { page.confirmDelete = true; unconfirm.restart() }
                }
            }
        }
    }

    Card {
        Layout.fillWidth: true
        padding: 20
        SettingRow {
            icon: Icons.refresh
            title: hub.t("Switch automatically")
            desc: hub.t("Picks the right profile when its game gets focus.")
            Toggle { checked: page.cfg.auto_switch_profiles; onToggled: function(on) { hub.set("auto_switch_profiles", on) } }
        }
        Caption { text: hub.t("Games for this profile (.exe names)"); Layout.topMargin: 4 }
        Area {
            id: games
            Layout.fillWidth: true
            Layout.preferredHeight: 110
            placeholderText: hub.t("One per line, e.g. cs2.exe — see Task Manager → Details")
            property string loadedFor: ""
            function load() { text = page.cfg.profile.exe_names.join("\n"); loadedFor = page.cfg.active_profile }
            Component.onCompleted: load()
            Connections { target: page; function onCfgChanged() { if (games.loadedFor !== page.cfg.active_profile) games.load() } }
            onCommitted: function(t) { hub.setLines("games", t) }
        }
    }
}
