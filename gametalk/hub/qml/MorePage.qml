import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Settings")
    subtitle: hub.t("Language, startup, sounds, learning mode and tools.")
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
                desc: hub.t("Small pop-up messages for warnings and tips.")
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
                Caption { text: hub.t("Learning mode") }
                SettingRow {
                    icon: Icons.book
                    title: hub.t("Save my phrasebook")
                    desc: hub.t("The only feature that stores what you said — on this PC only — so you can practise it.")
                    helpTopic: "learning"
                    Toggle { checked: page.f.learning_enabled; onToggled: function(on) { hub.set("features.learning_enabled", on) } }
                }
                Btn { text: hub.t("My phrasebook"); icon: Icons.book; small: true; onClicked: hub.phrasebook() }
            }

            Card {
                Layout.fillWidth: true
                Caption { text: hub.t("Tools") }
                Flow {
                    Layout.fillWidth: true
                    spacing: 10
                    Btn { text: hub.t("Self-test"); icon: Icons.pulse; small: true; onClicked: hub.selfTest() }
                    Btn { text: hub.t("Logs folder"); icon: Icons.folder; small: true; onClicked: hub.openLogs() }
                    Btn { text: hub.t("Desktop shortcut"); icon: Icons.link; small: true; onClicked: hub.createShortcut() }
                    Btn { text: hub.t("Help"); icon: Icons.help; small: true; onClicked: hub.openHelp("start") }
                }
            }

            Card {
                Layout.fillWidth: true
                Caption { text: hub.t("Close or quit") }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: Theme.muted
                    font.pixelSize: 12
                    text: hub.t("Closing this window keeps GameTalk running in the tray (hidden icons), so your key keeps working. Quit stops it completely.")
                }
                Btn { text: hub.t("Quit GameTalk"); icon: Icons.exit; kind: "danger"; small: true; onClicked: hub.quitApp() }
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
