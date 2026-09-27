import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Microphone")
    subtitle: hub.t("Which microphone GameTalk listens to. It's only open while you hold your key.")
    helpTopic: "microphone"

    readonly property var cfg: hub.config
    property var mics: hub.options("microphones")
    property bool testing: false
    property string result: ""
    property real level: 0

    Connections {
        target: hub
        function onMicTested(text) { page.testing = false; page.result = text }
        function onConfigChanged() { page.mics = hub.options("microphones") }
    }
    Timer {  // the live meter while the test records
        interval: 50
        repeat: true
        running: page.testing
        onTriggered: page.level = page.level * 0.55 + hub.micLevel * 0.45
        onRunningChanged: if (!running) page.level = 0
    }
    Timer { id: guard; interval: 12000; onTriggered: page.testing = false }

    Card {
        Layout.fillWidth: true
        padding: 20
        SettingRow {
            icon: Icons.mic
            title: hub.t("Input device")
            desc: hub.t("Pick your headset mic. After plugging one in, press Refresh.")
            RowLayout {
                spacing: 8
                Dropdown {
                    width: 320
                    items: page.mics
                    current: page.cfg.profile.microphone
                    onPicked: function(v) { hub.set("profile.microphone", v) }
                }
                Btn { icon: Icons.refresh; small: true; onClicked: hub.refreshMics() }
            }
        }
    }

    Card {
        Layout.fillWidth: true
        padding: 24
        RowLayout {
            Layout.fillWidth: true
            spacing: 26

            Item {  // mic badge with a level ring
                Layout.preferredWidth: 110
                Layout.preferredHeight: 110
                Rectangle {
                    anchors.centerIn: parent
                    width: 84 + page.level * 40
                    height: width
                    radius: width / 2
                    color: "transparent"
                    border.width: 3
                    border.color: Theme.accent
                    opacity: page.testing ? 0.25 + page.level * 0.75 : 0
                    Behavior on opacity { NumberAnimation { duration: 200 } }
                }
                Rectangle {
                    anchors.centerIn: parent
                    width: 80; height: 80; radius: 40
                    color: page.testing ? Theme.accent : Theme.surface2
                    Behavior on color { ColorAnimation { duration: 200 } }
                    Icon { anchors.centerIn: parent; path: Icons.mic; size: 36; color: page.testing ? "#ffffff" : Theme.textSoft }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10
                Text {
                    text: page.testing ? hub.t("Listening… say a sentence in Arabic") : hub.t("Test your microphone")
                    color: Theme.text
                    font.pixelSize: 18
                    font.weight: Font.Bold
                }
                Row {  // equalizer bars follow your voice
                    spacing: 4
                    height: 34
                    Repeater {
                        model: 24
                        delegate: Rectangle {
                            required property int index
                            readonly property real shape: 0.35 + 0.65 * Math.abs(Math.sin(index * 1.7 + 0.6))
                            width: 6
                            radius: 3
                            anchors.bottom: parent.bottom
                            height: 4 + (page.testing ? page.level * shape * 30 : 0)
                            color: index / 24 < page.level ? Theme.accent : Theme.track
                            Behavior on height { NumberAnimation { duration: 70 } }
                        }
                    }
                }
                Text {
                    visible: page.result !== ""
                    text: page.result
                    color: Theme.text
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Btn {
                    text: page.testing ? hub.t("Listening…") : hub.t("Test microphone (speak for 3 s)")
                    icon: Icons.mic
                    kind: "primary"
                    busy: page.testing
                    onClicked: { page.result = ""; page.testing = true; guard.restart(); hub.testMic(page.cfg.profile.microphone) }
                }
            }
        }
    }

    Card {
        Layout.fillWidth: true
        RowLayout {
            Icon { path: Icons.help; size: 16; color: Theme.accent }
            Caption { text: hub.t("If the test goes wrong") }
        }
        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Theme.textSoft
            font.pixelSize: 13
            text: hub.t("No sound: check the mic isn't muted in Windows (Settings → System → Sound). Words wrong: speak a little closer and louder, or try a bigger Whisper model or Azure Speech on the Engines page.")
        }
    }
}
