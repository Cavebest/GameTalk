import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Phrases and words")
    subtitle: hub.t("Ready-made sentences, your fixes for words that come out wrong, and game words. Saved per profile.")
    helpTopic: "phrases"

    readonly property var cfg: hub.config
    readonly property var prof: cfg.profile
    readonly property var f: cfg.features
    readonly property var hotkeys: hub.options("hotkeys")
    property var suggestions: hub.suggestions()
    Connections { target: hub; function onConfigChanged() { page.suggestions = hub.suggestions() } }

    // ---- quick phrases --------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 20
        SettingRow {
            icon: Icons.bubble
            title: hub.t("Quick phrases on keys")
            desc: hub.t("Press the key and the sentence appears at once — no speaking needed.")
            helpTopic: "phrases"
            Toggle { checked: page.f.quick_phrases_enabled; onToggled: function(on) { hub.set("features.quick_phrases_enabled", on) } }
        }
        PairList {
            id: phrases
            opacity: page.f.quick_phrases_enabled ? 1 : 0.5
            reloadKey: page.cfg.active_profile
            source: page.prof.quick_phrases.map(function(q) { return {a: q.key, b: q.text} })
            keyOptions: page.hotkeys
            bHint: hub.t("e.g. Enemy spotted!")
            addText: hub.t("Add phrase")
            onSave: function(rows) { hub.setPhrases(rows.map(function(r) { return {key: r.a, text: r.b} })) }
        }
        ColumnLayout {
            visible: page.suggestions.length > 0
            Layout.fillWidth: true
            spacing: 8
            RowLayout {
                spacing: 8
                Icon { path: Icons.sparkle; size: 15; color: Theme.accent }
                Caption { text: hub.t("You say these often — put them on a key?") }
            }
            Flow {
                Layout.fillWidth: true
                spacing: 8
                Repeater {
                    model: page.suggestions
                    delegate: Rectangle {
                        id: chip
                        required property string modelData
                        height: 32
                        width: ct.implicitWidth + 44
                        radius: 16
                        color: cm.containsMouse ? Theme.accentSoft : Theme.surface2
                        border.width: 1
                        border.color: cm.containsMouse ? Theme.accent : Theme.border
                        Behavior on color { ColorAnimation { duration: 140 } }
                        Row {
                            anchors.centerIn: parent
                            spacing: 6
                            Icon { path: Icons.plus; size: 14; color: Theme.accent; anchors.verticalCenter: parent.verticalCenter }
                            Text { id: ct; text: chip.modelData; color: Theme.text; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter }
                        }
                        MouseArea { id: cm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: phrases.add("", chip.modelData) }
                    }
                }
            }
        }
        SettingRow {
            title: hub.t("Suggest quick phrases for sentences you repeat")
            Toggle { checked: page.f.phrase_suggestions; onToggled: function(on) { hub.set("features.phrase_suggestions", on) } }
        }
    }

    // ---- corrections ------------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 20
        SettingRow {
            icon: Icons.type
            title: hub.t("Correction rules")
            desc: hub.t("A word keeps coming out wrong? Replace it in the English (whole words, one pass).")
            helpTopic: "corrections"
            Toggle { checked: page.f.corrections_enabled; onToggled: function(on) { hub.set("features.corrections_enabled", on) } }
        }
        PairList {
            opacity: page.f.corrections_enabled ? 1 : 0.5
            reloadKey: page.cfg.active_profile
            source: page.prof.corrections.map(function(c) { return {a: c.find, b: c.replace} })
            aHint: hub.t("wrong, e.g. Zafira")
            bHint: hub.t("right, e.g. ammo")
            addText: hub.t("Add rule")
            onSave: function(rows) { hub.setCorrections("english", rows.map(function(r) { return {find: r.a, replace: r.b} })) }
        }
    }

    Card {
        Layout.fillWidth: true
        padding: 20
        SettingRow {
            icon: Icons.language
            title: hub.t("Arabic dialect corrections")
            desc: hub.t("Dialect words become standard Arabic before translating (خليكم → ابقوا), so translators understand you better.")
            helpTopic: "corrections"
            Toggle { checked: page.f.arabic_corrections_enabled; onToggled: function(on) { hub.set("features.arabic_corrections_enabled", on) } }
        }
        PairList {
            opacity: page.f.arabic_corrections_enabled ? 1 : 0.5
            reloadKey: page.cfg.active_profile
            source: page.prof.arabic_corrections.map(function(c) { return {a: c.find, b: c.replace} })
            rtlText: true
            aHint: hub.t("dialect, e.g. هلق")
            bHint: hub.t("standard, e.g. الآن")
            addText: hub.t("Add rule")
            onSave: function(rows) { hub.setCorrections("arabic", rows.map(function(r) { return {find: r.a, replace: r.b} })) }
        }
    }

    // ---- vocabulary ---------------------------------------------------------------------------
    Card {
        Layout.fillWidth: true
        padding: 20
        SettingRow {
            icon: Icons.target
            title: hub.t("Gaming vocabulary")
            desc: hub.t("Game words (Medic, Flank, Fall back…) help Whisper and Azure Speech understand you. A hint only — nothing is ever replaced.")
            helpTopic: "translation"
            Toggle { checked: page.prof.vocabulary_enabled; onToggled: function(on) { hub.set("profile.vocabulary_enabled", on) } }
        }
        Area {
            id: vocab
            Layout.fillWidth: true
            Layout.preferredHeight: 170
            opacity: page.prof.vocabulary_enabled ? 1 : 0.5
            placeholderText: hub.t("One word or phrase per line")
            property string loadedFor: ""
            function load() { text = page.prof.vocabulary.join("\n"); loadedFor = page.cfg.active_profile }
            Component.onCompleted: load()
            Connections { target: page; function onCfgChanged() { if (vocab.loadedFor !== page.cfg.active_profile) vocab.load() } }
            onCommitted: function(t) { hub.setLines("vocabulary", t) }
        }
        Text {
            text: hub.t("Up to 50 entries; the first 24 are used.")
            color: Theme.faint
            font.pixelSize: 11
        }
    }
}
