import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Home")
    subtitle: hub.t("Everything at a glance — live while GameTalk runs.")

    readonly property var cfg: hub.config
    readonly property var st: hub.stats
    readonly property var prof: cfg.profile
    readonly property string phase: st.state === "disabled" ? "disabled"
        : st.loading ? "loading"
        : st.error ? "error"
        : (st.phase || "idle")
    readonly property color phaseColor: phase === "disabled" ? Theme.faint
        : phase === "recording" ? Theme.danger
        : phase === "error" ? Theme.danger
        : phase === "idle" ? Theme.ok
        : Theme.accent
    readonly property string hotkey: st.hotkey || prof.hotkey
    readonly property string speechName: prof.speech_provider === "azure" ? "Azure Speech" : "Whisper " + prof.model
    readonly property string translatorName: prof.translation_provider === "azure" ? "Azure Translator"
        : prof.translation_provider === "google" ? "Google Translate" : "Whisper"

    function statusTitle() {
        switch (phase) {
        case "loading": return hub.t("Loading the speech model…")
        case "error": return hub.t("Speech engine problem")
        case "disabled": return hub.t("GameTalk is paused")
        case "recording": return hub.t("Listening…")
        case "processing": return hub.t("Translating…")
        }
        if (prof.hotkey_mode === "voice") return hub.t("Ready — just talk (open mic)")
        if (prof.hotkey_mode === "toggle") return hub.tf("Ready — press {key} to talk", {key: hotkey})
        return hub.tf("Ready — hold {key} and speak", {key: hotkey})
    }
    function statusSub() {
        switch (phase) {
        case "loading": return hub.t("First time only: the model downloads once, then works offline.")
        case "error": return hub.t(st.error)
        case "disabled": return hub.t("Your key does nothing until you turn it back on. Press the button.")
        }
        return hub.tf("Profile: {name}", {name: st.profile || prof.name}) + "  ·  " + (st.engine || speechName)
    }
    function ago(ts) {
        var s = Math.max(0, Math.round(Date.now() / 1000 - ts))
        if (s < 10) return hub.t("just now")
        if (s < 60) return hub.tf("{n} s ago", {n: s})
        if (s < 3600) return hub.tf("{n} min ago", {n: Math.round(s / 60)})
        return hub.tf("{n} h ago", {n: Math.round(s / 3600)})
    }
    property real now: Date.now()
    Timer { interval: 5000; running: true; repeat: true; onTriggered: page.now = Date.now() }

    // ---- hero ---------------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 22
        RowLayout {
            Layout.fillWidth: true
            spacing: 22

            PowerButton {
                running: page.cfg.enabled
                busy: page.phase === "loading"
                live: page.phase === "recording"
                onClicked: hub.toggleEnabled()
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                RowLayout {
                    spacing: 10
                    Rectangle {
                        width: 10; height: 10; radius: 5
                        color: page.phaseColor
                        Behavior on color { ColorAnimation { duration: 250 } }
                        SequentialAnimation on scale {
                            running: page.phase === "idle" || page.phase === "recording"
                            loops: Animation.Infinite
                            NumberAnimation { to: 1.45; duration: page.phase === "recording" ? 380 : 900; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1; duration: page.phase === "recording" ? 380 : 900; easing.type: Easing.InOutSine }
                        }
                    }
                    Text {
                        text: page.statusTitle()
                        color: Theme.text
                        font.pixelSize: 21
                        font.weight: Font.Bold
                    }
                }
                Text {
                    text: page.statusSub()
                    color: Theme.muted
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }

            ColumnLayout {
                spacing: 6
                Layout.alignment: Qt.AlignVCenter
                Caption { text: hub.t("Talk key"); Layout.alignment: Qt.AlignHCenter }
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: Math.max(64, keyText.implicitWidth + 28)
                    height: 44
                    radius: 9
                    color: Theme.keyBase
                    Rectangle {
                        x: 3; y: 2; width: parent.width - 6; height: parent.height - 8; radius: 7
                        color: page.phase === "recording" ? Theme.accent : Theme.keyFace
                        border.width: 1; border.color: Theme.borderHover
                        Behavior on color { ColorAnimation { duration: 160 } }
                        Text {
                            id: keyText
                            anchors.centerIn: parent
                            text: prof.hotkey_mode === "voice" ? hub.t("Voice") : page.hotkey
                            color: Theme.text
                            font.pixelSize: 15
                            font.weight: Font.Bold
                            font.family: Theme.mono
                        }
                    }
                }
            }
        }
    }

    // ---- last translation -------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        accentEdge: true
        padding: 22
        RowLayout {
            Layout.fillWidth: true
            Caption { text: hub.t("Last translation"); Layout.fillWidth: true }
            Text {
                visible: !!page.st.last
                text: page.st.last ? (page.now, page.ago(page.st.last.at)) : ""
                color: Theme.faint
                font.pixelSize: 11
            }
        }
        TypeText {
            Layout.fillWidth: true
            full: page.st.last ? page.st.last.text : ""
            placeholder: hub.tf("Hold {key}, say something in Arabic, and it appears here.", {key: page.hotkey})
        }
        Text {
            visible: !!(page.st.last && page.st.last.extra)
            text: page.st.last ? page.st.last.extra : ""
            color: Theme.muted
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignRight
            Layout.fillWidth: true
            LayoutMirroring.enabled: false
        }
    }

    // ---- live numbers -------------------------------------------------------------------------
    GridLayout {
        Layout.fillWidth: true
        columns: 3
        columnSpacing: 16
        rowSpacing: 16

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            RowLayout {
                Icon { path: Icons.bolt; size: 16; color: Theme.accent }
                Caption { text: hub.t("Response time") }
            }
            RowLayout {
                spacing: 4
                CountUp {
                    value: {
                        var l = page.st.latencies || []
                        if (!l.length) return 0
                        var sum = 0
                        for (var i = 0; i < l.length; i++) sum += l[i]
                        return sum / l.length
                    }
                    decimals: 2
                    empty: !(page.st.latencies && page.st.latencies.length)
                    font.pixelSize: 30
                }
                Text { visible: !!(page.st.latencies && page.st.latencies.length); text: hub.t("s"); color: Theme.muted; font.pixelSize: 15; Layout.alignment: Qt.AlignBaseline }
            }
            Sparkline { Layout.fillWidth: true; points: page.st.latencies || [] }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            RowLayout {
                Icon { path: Icons.chart; size: 16; color: Theme.accent }
                Caption { text: hub.t("Translations today") }
            }
            CountUp { value: page.st.today || 0; font.pixelSize: 30 }
            Text {
                text: hub.t("Counted while GameTalk runs. Nothing you say is stored.")
                color: Theme.faint
                font.pixelSize: 11
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            RowLayout {
                Icon { path: Icons.engine; size: 16; color: Theme.accent }
                Caption { text: hub.t("Engine") }
            }
            Text {
                text: page.speechName
                color: Theme.text
                font.pixelSize: 19
                font.weight: Font.Bold
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Text {
                text: (page.st.engine || hub.t("not loaded")) + "  ·  " + page.translatorName
                color: Theme.muted
                font.pixelSize: 12
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Btn {
                text: hub.t("Change")
                icon: Icons.chevronRight
                small: true
                kind: "subtle"
                onClicked: page.navigate(1)
            }
        }
    }

    // ---- the path your words take ----------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 22
        RowLayout {
            Layout.fillWidth: true
            Caption { text: hub.t("The path of your voice"); Layout.fillWidth: true }
            PrivacyTag { profile: page.prof }
        }
        Pipeline {
            Layout.fillWidth: true
            nodes: [
                {icon: Icons.mic, title: hub.t("Your voice"), sub: page.hotkey},
                {icon: page.prof.speech_provider === "azure" ? Icons.cloud : Icons.pc, title: page.speechName, sub: hub.t("speech → text")},
                {icon: page.prof.translation_provider === "whisper-local" ? Icons.pc : Icons.cloud, title: page.translatorName, sub: hub.t("text → English")},
                {icon: Icons.overlay, title: hub.t("On screen"), sub: hub.t("over your game")}
            ]
            pulseKey: page.st.last ? page.st.last.at : 0
        }
    }

    // ---- free quota ---------------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 22
        visible: page.cfg.azure.speech_key || page.cfg.azure.translator_key || page.cfg.google.api_key
        Caption { text: hub.t("Free cloud quota this month") }
        RowLayout {
            Layout.fillWidth: true
            spacing: 28
            Repeater {
                model: [
                    {show: page.cfg.azure.speech_key, value: (page.st.usage || {}).speech || 0, name: "Azure Speech", note: hub.t("5 hours of audio")},
                    {show: page.cfg.azure.translator_key, value: (page.st.usage || {}).translator || 0, name: "Azure Translator", note: hub.t("2 million characters")},
                    {show: page.cfg.google.api_key, value: (page.st.usage || {}).google || 0, name: "Google Translate", note: hub.t("500,000 characters")}
                ]
                delegate: RowLayout {
                    required property var modelData
                    visible: modelData.show
                    spacing: 12
                    Ring { value: modelData.value; size: 66; line: 6 }
                    ColumnLayout {
                        spacing: 2
                        Text { text: modelData.name; color: Theme.text; font.pixelSize: 13; font.weight: Font.DemiBold }
                        Text { text: modelData.note; color: Theme.muted; font.pixelSize: 12 }
                    }
                }
            }
            Item { Layout.fillWidth: true }
        }
    }

    // ---- quick actions + tip -------------------------------------------------------------------
    RowLayout {
        Layout.fillWidth: true
        spacing: 16
        Card {
            Layout.fillWidth: true
            Layout.preferredWidth: 3
            Caption { text: hub.t("Quick actions") }
            Flow {
                Layout.fillWidth: true
                spacing: 10
                Btn { text: hub.t("Test microphone"); icon: Icons.mic; onClicked: page.navigate(2) }
                Btn { text: hub.t("Self-test"); icon: Icons.pulse; onClicked: hub.selfTest() }
                Btn { text: hub.t("Show overlay"); icon: Icons.eye; onClicked: hub.previewOverlay() }
                Btn { text: hub.t("My phrasebook"); icon: Icons.book; onClicked: hub.phrasebook() }
            }
        }
        TipCard { Layout.fillWidth: true; Layout.preferredWidth: 2; Layout.fillHeight: true }
    }
}
