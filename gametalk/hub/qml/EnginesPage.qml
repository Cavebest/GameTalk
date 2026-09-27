import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Engines")
    subtitle: hub.t("Choose who listens to your voice and who translates it — each step on its own.")
    helpTopic: "translation"

    readonly property var cfg: hub.config
    readonly property var prof: cfg.profile
    readonly property bool azureSpeech: prof.speech_provider === "azure"
    readonly property string tp: prof.translation_provider
    readonly property bool cloudTranslate: tp === "azure" || tp === "google"
    readonly property string missing: {
        if (azureSpeech && !(cfg.azure.speech_key && cfg.azure.speech_region)) return hub.t("Azure Speech needs its key and region.")
        if (tp === "azure" && !cfg.azure.translator_key) return hub.t("Azure Translator needs its key.")
        if (tp === "google" && !cfg.google.api_key) return hub.t("Google Translate needs an API key.")
        if (tp === "google" && cfg.google.model === "llm" && !cfg.google.project_id) return hub.t("The Translation LLM needs your Google Cloud project ID.")
        return ""
    }

    // ---- warning when a chosen cloud service has no key ---------------------------------------
    Rectangle {
        Layout.fillWidth: true
        visible: page.missing !== ""
        implicitHeight: warnRow.implicitHeight + 24
        radius: 12
        color: Theme.warnSoft
        border.width: 1
        border.color: Theme.warnBorder
        RowLayout {
            id: warnRow
            anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 14 }
            spacing: 12
            Icon { path: Icons.key; size: 20; color: Theme.warn }
            Text { text: page.missing; color: Theme.text; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            Btn { text: hub.t("Add key"); kind: "primary"; small: true; onClicked: page.navigate(6) }
        }
    }

    // ---- step 1 -------------------------------------------------------------------------------
    StepHeader { number: "1"; title: hub.t("Speech → text"); hint: hub.t("who listens to your voice") }
    RowLayout {
        Layout.fillWidth: true
        spacing: 16
        ChoiceCard {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            icon: Icons.pc
            title: hub.t("Whisper — on this PC")
            desc: hub.t("Free and private. Runs on your GPU or CPU and works offline.")
            badges: [{text: hub.t("Free"), tone: "ok"}, {text: hub.t("Offline"), tone: "ok"}]
            selected: !page.azureSpeech
            onChosen: hub.set("profile.speech_provider", "whisper-local")
        }
        ChoiceCard {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            icon: Icons.cloud
            title: "Azure Speech"
            desc: hub.t("Best for dialects: pick yours from 17 Arabic dialects. Needs internet.")
            badges: [{text: hub.t("Cloud"), tone: "cloud"}, {text: hub.t("Most accurate"), tone: "new"}]
            selected: page.azureSpeech
            onChosen: hub.set("profile.speech_provider", "azure")
        }
    }
    Card {
        Layout.fillWidth: true
        SettingRow {
            visible: !page.azureSpeech
            icon: Icons.engine
            title: hub.t("Whisper model")
            desc: hub.t("Bigger models understand dialects better but need more memory. Downloads once.")
            helpTopic: "speech"
            Dropdown {
                width: 260
                items: hub.options("models")
                current: page.prof.model
                onPicked: function(v) { hub.set("profile.model", v) }
            }
        }
        SettingRow {
            visible: !page.azureSpeech
            icon: Icons.bolt
            title: hub.t("Run on")
            desc: hub.t("Auto uses your NVIDIA GPU when available and falls back to the CPU.")
            Dropdown {
                width: 260
                items: hub.options("devices")
                current: page.cfg.compute_device
                onPicked: function(v) { hub.set("compute_device", v) }
            }
        }
        SettingRow {
            visible: page.azureSpeech
            icon: Icons.globe
            title: hub.t("Your dialect")
            desc: hub.t("Azure understands you best when it knows your dialect.")
            Dropdown {
                width: 260
                items: hub.options("locales")
                current: page.prof.azure_locale
                onPicked: function(v) { hub.set("profile.azure_locale", v) }
            }
        }
    }

    // ---- step 2 -------------------------------------------------------------------------------
    StepHeader { number: "2"; title: hub.t("Text → translation"); hint: hub.t("who turns it into English") }
    RowLayout {
        Layout.fillWidth: true
        spacing: 16
        ChoiceCard {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            icon: Icons.pc
            title: hub.t("Whisper — on this PC")
            desc: hub.t("Translates straight from your voice to English. Free and offline.")
            lockedNote: hub.t("Whisper can only translate from your voice, not from Azure's text.")
            enabled: !page.azureSpeech
            badges: [{text: hub.t("Free"), tone: "ok"}]
            selected: page.tp === "whisper-local"
            onChosen: hub.set("profile.translation_provider", "whisper-local")
        }
        ChoiceCard {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            icon: Icons.cloud
            title: "Azure Translator"
            desc: hub.t("2 million free characters a month. English or 14 other languages.")
            badges: [{text: hub.t("Cloud"), tone: "cloud"}]
            selected: page.tp === "azure"
            onChosen: hub.set("profile.translation_provider", "azure")
        }
        ChoiceCard {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            icon: Icons.translate
            title: "Google Translate"
            desc: hub.t("500,000 free characters a month. The LLM model understands dialect and context.")
            badges: [{text: hub.t("Cloud"), tone: "cloud"}, {text: hub.t("New"), tone: "new"}]
            selected: page.tp === "google"
            onChosen: hub.set("profile.translation_provider", "google")
        }
    }
    Card {
        Layout.fillWidth: true
        SettingRow {
            icon: Icons.globe
            title: hub.t("Translate to")
            desc: page.cloudTranslate ? hub.t("Your teammates' language.") : hub.t("Whisper always translates to English.")
            Dropdown {
                width: 260
                enabled: page.cloudTranslate
                items: hub.options("targets")
                current: page.prof.target_language
                onPicked: function(v) { hub.set("profile.target_language", v) }
            }
        }
        SettingRow {
            visible: page.tp === "google"
            icon: Icons.sparkle
            title: hub.t("Google model")
            desc: page.cfg.google.model === "llm" ? hub.t("Smarter with dialect and context. Needs your project ID (Cloud keys page).")
                                                   : hub.t("Google's standard translation. Fast, and the cheapest.")
            Segmented {
                items: [{value: "nmt", label: hub.t("Standard")}, {value: "llm", label: "LLM"}]
                current: page.cfg.google.model
                onPicked: function(v) { hub.set("google.model", v) }
            }
        }
        SettingRow {
            icon: Icons.target
            title: hub.t("Gaming mode")
            desc: hub.t("Short, casual callouts like real squad chat.")
            Toggle { checked: page.prof.gaming_mode; onToggled: function(on) { hub.set("profile.gaming_mode", on) } }
        }
        SettingRow {
            icon: Icons.language
            title: hub.t("Pronunciation helper")
            desc: hub.t("Shows the English written in Arabic letters, so you can say it.")
            helpTopic: "pronunciation"
            Toggle { checked: page.cfg.features.pronunciation_enabled; onToggled: function(on) { hub.set("features.pronunciation_enabled", on) } }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        PrivacyTag { profile: page.prof }
        Item { Layout.fillWidth: true }
    }
}
