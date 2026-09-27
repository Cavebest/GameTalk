import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Settings")
    subtitle: hub.t("Language, profiles, startup and the detailed settings pages.")
    helpTopic: "general"

    readonly property var cfg: hub.config
    readonly property var f: cfg.features

    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 980 ? 2 : 1
        columnSpacing: 16
        rowSpacing: 16

        Card {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.alignment: Qt.AlignTop
            Caption { text: hub.t("General") }
            SettingRow {
                icon: Icons.language
                title: hub.t("Interface language")
                Segmented {
                    items: [{value: "auto", label: hub.t("Auto")}, {value: "en", label: "English"}, {value: "ar", label: "العربية"}]
                    current: page.f.ui_language
                    onPicked: function(v) { hub.setLanguage(v) }
                }
            }
            SettingRow {
                icon: Icons.power
                title: hub.t("Start with Windows")
                desc: hub.t("GameTalk waits in the tray, ready for your first game.")
                Toggle { checked: hub.autostart; onToggled: function(on) { hub.setAutostart(on) } }
            }
            SettingRow {
                icon: Icons.bubble
                title: hub.t("Tray notifications")
                Toggle { checked: page.f.tray_notifications; onToggled: function(on) { hub.set("features.tray_notifications", on) } }
            }
            SettingRow {
                icon: Icons.speaker
                title: hub.t("Sound cues")
                desc: hub.t("A soft beep when recording starts and stops.")
                Toggle { checked: page.f.sound_cues; onToggled: function(on) { hub.set("features.sound_cues", on) } }
            }
            LabeledSlider {
                visible: page.f.sound_cues
                title: hub.t("Sound volume")
                from: 0; to: 100
                bound: page.f.sound_volume
                unit: "%"
                onCommitted: function(v) { hub.set("features.sound_volume", v) }
            }
            SettingRow {
                icon: Icons.link
                title: hub.t("Copy translations to the clipboard")
                desc: hub.t("Paste them into text chat yourself. Nothing is typed for you.")
                Toggle { checked: page.f.copy_to_clipboard; onToggled: function(on) { hub.set("features.copy_to_clipboard", on) } }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.alignment: Qt.AlignTop
            spacing: 16

            Card {
                Layout.fillWidth: true
                Caption { text: hub.t("Profiles") }
                SettingRow {
                    icon: Icons.target
                    title: hub.t("Active profile")
                    desc: hub.t("Each game can have its own key, engines and overlay.")
                    Dropdown {
                        width: 200
                        items: page.cfg.profiles.map(function(n) { return {value: n, label: n} })
                        current: page.cfg.active_profile
                        onPicked: function(v) { hub.setProfile(v) }
                    }
                }
                SettingRow {
                    icon: Icons.refresh
                    title: hub.t("Switch automatically")
                    desc: hub.t("Picks the right profile when its game gets focus.")
                    Toggle { checked: page.cfg.auto_switch_profiles; onToggled: function(on) { hub.set("auto_switch_profiles", on) } }
                }
                Btn { text: hub.t("Manage profiles and games"); icon: Icons.sliders; small: true; onClicked: hub.openSettings("games") }
            }

            Card {
                Layout.fillWidth: true
                Caption { text: hub.t("Tools") }
                Flow {
                    Layout.fillWidth: true
                    spacing: 10
                    Btn { text: hub.t("Self-test"); icon: Icons.pulse; small: true; onClicked: hub.selfTest() }
                    Btn { text: hub.t("My phrasebook"); icon: Icons.book; small: true; onClicked: hub.phrasebook() }
                    Btn { text: hub.t("Logs folder"); icon: Icons.folder; small: true; onClicked: hub.openLogs() }
                    Btn { text: hub.t("Desktop shortcut"); icon: Icons.link; small: true; onClicked: hub.createShortcut() }
                }
            }
        }
    }

    Caption { text: hub.t("Detailed settings"); Layout.topMargin: 4 }
    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 1000 ? 4 : 2
        columnSpacing: 12
        rowSpacing: 12
        Repeater {
            model: [
                {tab: "microphone", icon: Icons.mic},
                {tab: "speech", icon: Icons.engine},
                {tab: "phrases", icon: Icons.bubble},
                {tab: "corrections", icon: Icons.type},
                {tab: "quicktext", icon: Icons.keyboard},
                {tab: "learning", icon: Icons.book},
                {tab: "overlay", icon: Icons.overlay},
                {tab: "games", icon: Icons.target}
            ]
            delegate: Rectangle {
                id: tile
                required property var modelData
                readonly property string topic: modelData.tab === "games" ? "profiles" : modelData.tab
                Layout.fillWidth: true
                implicitHeight: 92
                radius: 12
                color: tm.containsMouse ? Theme.surface2 : Theme.surface
                border.width: 1
                border.color: tm.containsMouse ? Theme.accent : Theme.border
                scale: tm.pressed ? 0.97 : 1
                Behavior on color { ColorAnimation { duration: 160 } }
                Behavior on border.color { ColorAnimation { duration: 160 } }
                Behavior on scale { NumberAnimation { duration: 120 } }
                ColumnLayout {
                    anchors { fill: parent; margins: 14 }
                    spacing: 4
                    RowLayout {
                        Icon { path: tile.modelData.icon; size: 18; color: tm.containsMouse ? Theme.accent : Theme.textSoft }
                        Item { Layout.fillWidth: true }
                        Icon {
                            path: Icons.external
                            size: 14
                            color: Theme.faint
                            opacity: tm.containsMouse ? 1 : 0
                            Behavior on opacity { NumberAnimation { duration: 160 } }
                        }
                    }
                    Text { text: hub.helpTitle(tile.topic); color: Theme.text; font.pixelSize: 13; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                    Text { text: hub.helpSummary(tile.topic); color: Theme.muted; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                }
                MouseArea {
                    id: tm
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: hub.openSettings(tile.modelData.tab)
                }
            }
        }
    }

    Card {
        Layout.fillWidth: true
        Layout.topMargin: 4
        RowLayout {
            Layout.fillWidth: true
            spacing: 14
            Logo { size: 44 }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text { text: hub.t("GameTalk Translator") + "  " + hub.version; color: Theme.text; font.pixelSize: 15; font.weight: Font.Bold }
                Text { text: hub.copyright + " · " + hub.t("Released under the MIT License."); color: Theme.muted; font.pixelSize: 12 }
            }
            Btn { text: "GitHub"; icon: Icons.external; small: true; onClicked: hub.openUrl(hub.authorUrl) }
        }
    }
}
