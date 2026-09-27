import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Hotkeys")
    subtitle: hub.t("Click a key, then press the key you want. Esc cancels.")
    helpTopic: "hotkey"

    readonly property var cfg: hub.config
    readonly property var prof: cfg.profile
    readonly property var f: cfg.features
    readonly property var keys: hub.options("hotkeys").map(function(o) { return o.value })

    Card {
        Layout.fillWidth: true
        padding: 22
        RowLayout {
            Layout.fillWidth: true
            spacing: 24
            ColumnLayout {
                spacing: 8
                Caption { text: hub.t("Talk key") }
                KeyCapture {
                    id: talkKey
                    target: "talk"
                    implicitWidth: 150
                    current: page.prof.hotkey
                    allowed: page.keys
                    enabled: page.prof.hotkey_mode !== "voice"
                    opacity: enabled ? 1 : 0.4
                    onPicked: function(k) { hub.set("profile.hotkey", k) }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8
                Caption { text: hub.t("How it works") }
                Segmented {
                    items: hub.options("hotkeyModes")
                    current: page.prof.hotkey_mode
                    onPicked: function(v) { hub.set("profile.hotkey_mode", v) }
                }
                Text {
                    text: page.prof.hotkey_mode === "push" ? hub.t("Hold the key while you speak, let go to translate.")
                        : page.prof.hotkey_mode === "toggle" ? hub.t("Press once to start, press again to translate.")
                        : hub.t("No key needed: GameTalk hears when you start and stop talking. The key mutes it.")
                    color: Theme.muted
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
        Text {
            visible: talkKey.error !== ""
            text: talkKey.error
            color: Theme.danger
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        LabeledSlider {
            visible: page.prof.hotkey_mode === "voice"
            title: hub.t("Open-mic sensitivity")
            from: 0; to: 100
            bound: page.f.voice_sensitivity
            unit: "%"
            onCommitted: function(v) { hub.set("features.voice_sensitivity", v) }
        }
    }

    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 900 ? 2 : 1
        columnSpacing: 16
        rowSpacing: 16

        Card {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            SettingRow {
                icon: Icons.refresh
                title: hub.t("Replay key")
                desc: hub.t("Shows your last translation again.")
                helpTopic: "replay"
                Toggle { checked: page.f.replay_enabled; onToggled: function(on) { hub.set("features.replay_enabled", on) } }
            }
            KeyCapture {
                id: replayKey
                target: "replay"
                implicitWidth: 130
                current: page.f.replay_hotkey
                allowed: page.keys
                enabled: page.f.replay_enabled
                opacity: enabled ? 1 : 0.4
                onPicked: function(k) { hub.set("features.replay_hotkey", k) }
            }
            Text { visible: replayKey.error !== ""; text: replayKey.error; color: Theme.danger; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }

        Card {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            SettingRow {
                icon: Icons.type
                title: hub.t("Quick text key")
                desc: hub.t("Opens a box: type Arabic, press Enter, get English.")
                helpTopic: "quicktext"
                Toggle { checked: page.f.quick_text_enabled; onToggled: function(on) { hub.set("features.quick_text_enabled", on) } }
            }
            KeyCapture {
                id: textKey
                target: "quicktext"
                implicitWidth: 130
                current: page.f.quick_text_hotkey
                allowed: page.keys
                enabled: page.f.quick_text_enabled
                opacity: enabled ? 1 : 0.4
                onPicked: function(k) { hub.set("features.quick_text_hotkey", k) }
            }
            Text { visible: textKey.error !== ""; text: textKey.error; color: Theme.danger; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }

    Card {
        Layout.fillWidth: true
        SettingRow {
            icon: Icons.gamepad
            title: hub.t("Game controller")
            desc: hub.t("Hold a button on your Xbox / XInput controller to talk.")
            helpTopic: "gamepad"
            Toggle { checked: page.f.gamepad_enabled; onToggled: function(on) { hub.set("features.gamepad_enabled", on) } }
        }
        Flow {
            Layout.fillWidth: true
            spacing: 8
            opacity: page.f.gamepad_enabled ? 1 : 0.4
            Behavior on opacity { NumberAnimation { duration: 200 } }
            Repeater {
                model: hub.options("gamepad")
                delegate: Rectangle {
                    id: pad
                    required property var modelData
                    readonly property bool chosen: page.f.gamepad_button === modelData.value
                    width: Math.max(44, bl.implicitWidth + 22)
                    height: 36
                    radius: 18
                    color: chosen ? Theme.accent : (pm.containsMouse ? Theme.raised : Theme.surface2)
                    border.width: 1
                    border.color: chosen ? Theme.accent : Theme.border
                    scale: pm.pressed ? 0.92 : 1
                    Behavior on color { ColorAnimation { duration: 160 } }
                    Behavior on scale { NumberAnimation { duration: 120 } }
                    Text { id: bl; anchors.centerIn: parent; text: pad.modelData.label; color: pad.chosen ? "#ffffff" : Theme.textSoft; font.pixelSize: 12; font.weight: Font.Bold }
                    MouseArea {
                        id: pm
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: page.f.gamepad_enabled
                        cursorShape: Qt.PointingHandCursor
                        onClicked: hub.set("features.gamepad_button", pad.modelData.value)
                    }
                }
            }
        }
    }

    Card {
        Layout.fillWidth: true
        SettingRow {
            icon: Icons.refresh
            title: hub.t("Controller replay button")
            desc: hub.t("Optional: a second controller button that shows your last translation again.")
            Dropdown {
                width: 200
                enabled: page.f.gamepad_enabled
                items: hub.options("gamepadReplay")
                current: page.f.gamepad_replay_button
                onPicked: function(v) { hub.set("features.gamepad_replay_button", v) }
            }
        }
        SettingRow {
            icon: Icons.shield
            title: hub.t("Stuck-key protection")
            desc: hub.t("Stops the recording even if Windows misses the moment you let go of the key.")
            Toggle { checked: page.f.stuck_key_protection; onToggled: function(on) { hub.set("features.stuck_key_protection", on) } }
        }
    }

    Text {
        text: hub.t("Keys still reach your game, so pick one the game doesn't use. If a game runs as administrator, run GameTalk as administrator too.")
        color: Theme.faint
        font.pixelSize: 12
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
}
