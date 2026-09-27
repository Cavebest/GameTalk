import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Cloud keys")
    subtitle: hub.t("Only needed if you choose Azure or Google. Keys are encrypted with your Windows account and never logged.")
    helpTopic: "azure"

    readonly property var cfg: hub.config
    property var azureResult: []
    property var googleResult: []
    property bool azureBusy: false
    property bool googleBusy: false

    Connections {
        target: hub
        function onTestDone(which, lines) {
            if (which === "azure") { page.azureResult = lines; page.azureBusy = false }
            else { page.googleResult = lines; page.googleBusy = false }
        }
    }

    // ---- Azure ---------------------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 22
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Rectangle {
                width: 40; height: 40; radius: 11
                color: Theme.surface2
                Icon { anchors.centerIn: parent; path: Icons.cloud; size: 21; color: Theme.azure }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Text { text: "Microsoft Azure"; color: Theme.text; font.pixelSize: 16; font.weight: Font.Bold; Layout.fillWidth: true }
                Text { text: hub.t("Speech: 5 free hours a month · Translator: 2 million free characters"); color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
            Btn { text: hub.t("How to get keys"); icon: Icons.help; small: true; kind: "subtle"; onClicked: hub.openHelp("azure") }
        }
        Caption { text: "Azure Speech"; Layout.topMargin: 6 }
        SecretField { title: hub.t("Speech key"); path: "azure.speech_key"; saved: page.cfg.azure.speech_key }
        RegionField { title: hub.t("Speech region"); path: "azure.speech_region"; value: page.cfg.azure.speech_region; hint: hub.t("e.g. westeurope, uaenorth, eastus") }
        Caption { text: "Azure Translator"; Layout.topMargin: 6 }
        SecretField { title: hub.t("Translator key"); path: "azure.translator_key"; saved: page.cfg.azure.translator_key }
        RegionField { title: hub.t("Translator region"); path: "azure.translator_region"; value: page.cfg.azure.translator_region; hint: hub.t("e.g. westeurope, or global") }
        RowLayout {
            Layout.fillWidth: true
            Btn {
                text: hub.t("Test connection")
                icon: Icons.pulse
                busy: page.azureBusy
                enabled: page.cfg.azure.speech_key || page.cfg.azure.translator_key
                onClicked: { page.azureBusy = true; page.azureResult = []; hub.testAzure() }
            }
            Item { Layout.fillWidth: true }
        }
        TestResults { lines: page.azureResult }
    }

    // ---- Google ------------------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 22
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Rectangle {
                width: 40; height: 40; radius: 11
                color: Theme.surface2
                Icon { anchors.centerIn: parent; path: Icons.translate; size: 21; color: Theme.google }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                RowLayout {
                    spacing: 8
                    Text { text: "Google Translate"; color: Theme.text; font.pixelSize: 16; font.weight: Font.Bold }
                    Rectangle {
                        width: nt.implicitWidth + 14; height: 20; radius: 10
                        color: Theme.accentSoft; border.width: 1; border.color: Theme.accent
                        Text { id: nt; anchors.centerIn: parent; text: hub.t("New"); color: Theme.accent; font.pixelSize: 11; font.weight: Font.Bold }
                    }
                }
                Text { text: hub.t("500,000 free characters a month (about 16,000 sentences). Needs billing on in Google Cloud."); color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            }
            Btn { text: hub.t("How to get a key"); icon: Icons.help; small: true; kind: "subtle"; onClicked: hub.openHelp("azure") }
        }
        SecretField { title: hub.t("API key"); path: "google.api_key"; saved: page.cfg.google.api_key }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Text { text: hub.t("Model"); color: Theme.textSoft; font.pixelSize: 13; Layout.preferredWidth: 150 }
            Segmented {
                items: [{value: "nmt", label: hub.t("Standard")}, {value: "llm", label: hub.t("Translation LLM")}]
                current: page.cfg.google.model
                onPicked: function(v) { hub.set("google.model", v) }
            }
            Item { Layout.fillWidth: true }
        }
        Text {
            text: page.cfg.google.model === "llm"
                  ? hub.t("Translation LLM: smarter with dialect and context. $10 per million characters in + $10 out, from the same free monthly credit.")
                  : hub.t("Standard: fast and cheap. The first 500,000 characters each month are free, then $20 per million.")
            color: Theme.muted
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        RegionField {
            visible: page.cfg.google.model === "llm" || page.cfg.profile.speech_provider === "google"
            title: hub.t("Project ID")
            path: "google.project_id"
            value: page.cfg.google.project_id
            hint: hub.t("e.g. my-project-123456")
        }
        ColumnLayout {  // Chirp 3 logs in with a service account, not the API key
            Layout.fillWidth: true
            visible: page.cfg.profile.speech_provider === "google" || page.cfg.google.service_account
            spacing: 8
            Caption { text: hub.t("Google Chirp 3 login"); Layout.topMargin: 6 }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Text { text: hub.t("Service account"); color: Theme.textSoft; font.pixelSize: 13; Layout.preferredWidth: 150 }
                Rectangle {
                    visible: page.cfg.google.service_account
                    Layout.fillWidth: true
                    implicitHeight: 38
                    radius: 8
                    color: Theme.okSoft
                    border.width: 1
                    border.color: Theme.okBorder
                    RowLayout {
                        anchors { fill: parent; leftMargin: 12; rightMargin: 6 }
                        Icon { path: Icons.lock; size: 15; color: Theme.ok }
                        Text { text: hub.t("Saved and encrypted"); color: Theme.ok; font.pixelSize: 12; font.weight: Font.DemiBold; Layout.fillWidth: true }
                        Btn { text: hub.t("Remove"); small: true; kind: "subtle"; icon: Icons.trash; onClicked: hub.clearSecret("google.service_account") }
                    }
                }
                Btn {
                    visible: !page.cfg.google.service_account
                    text: hub.t("Load .json file…")
                    icon: Icons.upload
                    kind: "primary"
                    small: true
                    onClicked: hub.loadServiceAccount()
                }
                Item { visible: !page.cfg.google.service_account; Layout.fillWidth: true }
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Theme.muted
                font.pixelSize: 12
                text: hub.t("Google Cloud → IAM & Admin → Service Accounts → Create service account → role “Cloud Speech Client” → open it → Keys → Add key → JSON. Load the downloaded file here. Keep it private: it's like a password.")
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Btn {
                text: hub.t("Test Google")
                icon: Icons.pulse
                busy: page.googleBusy
                enabled: page.cfg.google.api_key || page.cfg.google.service_account
                onClicked: { page.googleBusy = true; page.googleResult = []; hub.testGoogle() }
            }
            Item { Layout.fillWidth: true }
        }
        TestResults { lines: page.googleResult }
    }

    Card {
        Layout.fillWidth: true
        padding: 20
        RowLayout {
            Layout.fillWidth: true
            Caption { text: hub.t("Free quota used this month"); Layout.fillWidth: true }
            Btn { text: hub.t("Reset counter"); icon: Icons.refresh; small: true; kind: "subtle"; onClicked: hub.resetUsage() }
        }
        Repeater {
            model: [
                {name: "Azure Speech", value: (hub.stats.usage || {}).speech || 0, note: hub.t("5 hours of audio")},
                {name: "Azure Translator", value: (hub.stats.usage || {}).translator || 0, note: hub.t("2 million characters")},
                {name: "Google Translate", value: (hub.stats.usage || {}).google || 0, note: hub.t("500,000 characters")}
            ]
            delegate: ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: 4
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: modelData.name; color: Theme.text; font.pixelSize: 13; Layout.fillWidth: true }
                    Text { text: Math.round(modelData.value * 100) + "% · " + modelData.note; color: Theme.muted; font.pixelSize: 12 }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 6
                    radius: 3
                    color: Theme.track
                    Rectangle {
                        height: parent.height
                        radius: 3
                        width: parent.width * Math.min(1, modelData.value)
                        x: hub.rtl ? parent.width - width : 0
                        color: modelData.value >= 1 ? Theme.danger : modelData.value >= 0.8 ? Theme.warn : Theme.accent
                        Behavior on width { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            visible: ((hub.stats.usage || {}).googleSpeechMinutes || 0) > 0
            Text { text: "Google Chirp 3"; color: Theme.text; font.pixelSize: 13; Layout.fillWidth: true }
            Text {
                readonly property real minutes: (hub.stats.usage || {}).googleSpeechMinutes || 0
                text: hub.tf("{min} min · about ${cost}", {min: minutes.toFixed(1), cost: (minutes * 0.016).toFixed(2)})
                color: Theme.muted
                font.pixelSize: 12
            }
        }
        SettingRow {
            title: hub.t("Usage counter and quota warnings")
            Toggle { checked: page.cfg.features.azure_usage_tracking; onToggled: function(on) { hub.set("features.azure_usage_tracking", on) } }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Icon { path: Icons.shield; size: 18; color: Theme.ok }
        Text {
            text: hub.t("Nothing is sent to a cloud service unless a profile uses it. Azure Speech gets your push-to-talk audio; translators get only text.")
            color: Theme.muted
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
