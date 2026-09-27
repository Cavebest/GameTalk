import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Teammates")
    subtitle: hub.t("Subtitles for what you hear: GameTalk listens to your PC's sound and shows teammates' speech in Arabic.")
    helpTopic: "teammates"

    readonly property var cfg: hub.config
    readonly property var tm: cfg.teammates

    Card {
        Layout.fillWidth: true
        padding: 22
        RowLayout {
            Layout.fillWidth: true
            spacing: 18
            Rectangle {
                Layout.preferredWidth: 54
                Layout.preferredHeight: 54
                radius: 14
                color: page.tm.enabled ? Theme.accent : Theme.surface2
                Behavior on color { ColorAnimation { duration: 220 } }
                Icon { anchors.centerIn: parent; path: Icons.speaker; size: 28; color: page.tm.enabled ? "#ffffff" : Theme.muted }
                // sound waves while on
                Repeater {
                    model: 2
                    delegate: Rectangle {
                        id: ripple
                        required property int index
                        anchors.centerIn: parent
                        width: 54; height: 54; radius: 14
                        color: "transparent"
                        border.width: 2
                        border.color: Theme.accent
                        opacity: 0
                        visible: page.tm.enabled
                        ParallelAnimation {
                            running: page.tm.enabled
                            loops: Animation.Infinite
                            SequentialAnimation {
                                PauseAnimation { duration: index * 700 }
                                NumberAnimation { target: ripple; property: "scale"; from: 1; to: 1.5; duration: 1400; easing.type: Easing.OutCubic }
                            }
                            SequentialAnimation {
                                PauseAnimation { duration: index * 700 }
                                NumberAnimation { target: ripple; property: "opacity"; from: 0.6; to: 0; duration: 1400 }
                            }
                        }
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Text {
                    text: page.tm.enabled ? hub.t("Teammate subtitles are on") : hub.t("Teammate subtitles are off")
                    color: Theme.text
                    font.pixelSize: 18
                    font.weight: Font.Bold
                }
                Text {
                    text: hub.t("It pauses while you talk and handles one sentence at a time, so games stay smooth.")
                    color: Theme.muted
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
            Toggle { checked: page.tm.enabled; onToggled: function(on) { hub.set("teammates.enabled", on) } }
        }
    }

    Card {
        Layout.fillWidth: true
        SettingRow {
            icon: Icons.speaker
            title: hub.t("Listen to")
            desc: hub.t("The speakers or headset your game and Discord play through.")
            Dropdown {
                width: 300
                items: hub.options("speakers")
                current: page.tm.device
                onPicked: function(v) { hub.set("teammates.device", v) }
            }
        }
    }

    Caption { text: hub.t("Who understands them") }
    RowLayout {
        Layout.fillWidth: true
        spacing: 16
        ChoiceCard {
            Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.fillHeight: true
            icon: Icons.pc
            title: hub.t("Whisper — on this PC")
            desc: hub.t("Free and private, uses your GPU for a moment per sentence.")
            badges: [{text: hub.t("Free"), tone: "ok"}]
            selected: page.tm.recognizer === "whisper-local"
            onChosen: hub.set("teammates.recognizer", "whisper-local")
        }
        ChoiceCard {
            Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.fillHeight: true
            icon: Icons.cloud
            title: "Azure Speech"
            desc: hub.t("Very accurate English recognition. Gunfire and music are never sent.")
            badges: [{text: hub.t("Cloud"), tone: "cloud"}]
            selected: page.tm.recognizer === "azure"
            onChosen: hub.set("teammates.recognizer", "azure")
        }
    }

    Card {
        Layout.fillWidth: true
        SettingRow {
            icon: Icons.translate
            title: hub.t("Translate with")
            desc: hub.t("The offline model is free and private; cloud services are more natural.")
            Dropdown {
                width: 280
                items: hub.options("teamTranslators")
                current: page.tm.translator
                onPicked: function(v) { hub.set("teammates.translator", v) }
            }
        }
        SettingRow {
            icon: Icons.globe
            title: hub.t("Subtitle language")
            desc: page.tm.translator === "local" ? hub.t("The offline model translates English to Arabic.") : hub.t("The language you read best.")
            Dropdown {
                width: 280
                enabled: page.tm.translator === "azure" || page.tm.translator === "google"
                items: hub.options("targets")
                current: page.tm.target_language
                onPicked: function(v) { hub.set("teammates.target_language", v) }
            }
        }
        SettingRow {
            icon: Icons.type
            title: hub.t("Also show the original English")
            desc: hub.t("Handy for learning: the English line appears under the translation.")
            Toggle { checked: page.tm.show_original; onToggled: function(on) { hub.set("teammates.show_original", on) } }
        }
        LabeledSlider {
            title: hub.t("Sensitivity (higher picks up quieter voices)")
            from: 0; to: 100
            bound: page.tm.sensitivity
            unit: "%"
            onCommitted: function(v) { hub.set("teammates.sensitivity", v) }
        }
    }

    Card {
        Layout.fillWidth: true
        Caption { text: hub.t("Where the subtitles appear") }
        RowLayout {
            Layout.fillWidth: true
            spacing: 22
            PositionPicker {
                current: page.tm.position
                onPicked: function(v) { hub.set("teammates.position", v) }
            }
            ColumnLayout {
                Layout.fillWidth: true
                LabeledSlider { title: hub.t("Distance from the edge"); from: 0; to: 800; stepSize: 4; bound: page.tm.offset_y; unit: " px"; onCommitted: function(v) { hub.set("teammates.offset_y", v) } }
                LabeledSlider { title: hub.t("Text size"); from: 10; to: 40; bound: page.tm.font_size; unit: " pt"; onCommitted: function(v) { hub.set("teammates.font_size", v) } }
                LabeledSlider { title: hub.t("Stays on screen"); from: 1; to: 15; bound: page.tm.display_seconds; unit: " " + hub.t("s"); onCommitted: function(v) { hub.set("teammates.display_seconds", v) } }
            }
        }
    }
}
