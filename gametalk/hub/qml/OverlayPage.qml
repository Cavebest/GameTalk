import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Overlay")
    subtitle: hub.t("How your translation looks over the game. The preview updates as you drag.")
    helpTopic: "overlay"

    readonly property var cfg: hub.config
    readonly property var prof: cfg.profile
    readonly property var style: cfg.overlay
    property bool moving: false
    Component.onDestruction: if (moving) hub.moveOverlay(false)

    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 900 ? 2 : 1
        columnSpacing: 16
        rowSpacing: 16

        // ---- live preview -----------------------------------------------------------------
        Card {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            padding: 14
            RowLayout {
                Layout.fillWidth: true
                Caption { text: hub.t("Live preview"); Layout.fillWidth: true }
                Btn { text: hub.t("Show on screen"); icon: Icons.eye; small: true; onClicked: hub.previewOverlay() }
            }
            GameScene {
                id: scene
                Layout.fillWidth: true
                Layout.preferredHeight: width * 9 / 16
                position: page.prof.overlay_position
                offsetX: offX.value
                offsetY: offY.value
                fontSize: fontS.value
                maxWidth: widthS.value
                bgOpacity: bgS.value / 100
                textOpacity: textS.value / 100
                radiusPx: radiusS.value
                accent: page.style.accent_color
                textColor: page.style.text_color
                bgColor: page.style.background_color
                outline: page.style.text_outline
                showPron: page.cfg.features.pronunciation_enabled
            }
            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: hub.t("Tip: to place it exactly, use “Move with the mouse” and drag it on your real screen.")
                    color: Theme.faint
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Btn {
                    text: page.moving ? hub.t("Done") : hub.t("Move with the mouse")
                    icon: page.moving ? Icons.check : Icons.move
                    small: true
                    kind: page.moving ? "primary" : "subtle"
                    onClicked: { page.moving = !page.moving; hub.moveOverlay(page.moving) }
                }
            }
        }

        // ---- controls ------------------------------------------------------------------------
        Card {
            Layout.fillWidth: true
            Layout.preferredWidth: 380
            Layout.maximumWidth: page.width > 900 ? 400 : 100000
            Layout.alignment: Qt.AlignTop
            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                ColumnLayout {
                    spacing: 6
                    Caption { text: hub.t("Position") }
                    PositionPicker {
                        current: page.prof.overlay_position
                        onPicked: function(v) { hub.set("profile.overlay_position", v) }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Caption { text: hub.t("Accent colour") }
                    Swatches {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 150
                        colors: ["#ff5a1f", "#38bdf8", "#22c55e", "#a855f7", "#f43f5e", "#facc15", "#14b8a6", "#ffffff"]
                        current: page.style.accent_color
                        onPicked: function(c) { hub.set("overlay.accent_color", c) }
                    }
                    Caption { text: hub.t("Text colour"); Layout.topMargin: 6 }
                    Swatches {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 150
                        colors: ["#f5f7fa", "#ffe082", "#b3e5fc", "#c8facc"]
                        current: page.style.text_color
                        onPicked: function(c) { hub.set("overlay.text_color", c) }
                    }
                    Caption { text: hub.t("Background colour"); Layout.topMargin: 6 }
                    Swatches {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 150
                        colors: ["#0c0e14", "#000000", "#1a1025", "#0b1d2a"]
                        current: page.style.background_color
                        onPicked: function(c) { hub.set("overlay.background_color", c) }
                    }
                }
            }
            LabeledSlider { id: offX; title: hub.t("Sideways shift"); from: -800; to: 800; stepSize: 10; bound: page.prof.overlay_offset_x; unit: " px"; onCommitted: function(v) { hub.set("profile.overlay_offset_x", v) } }
            LabeledSlider { id: offY; title: hub.t("Distance from the edge"); from: -200; to: 800; stepSize: 4; bound: page.prof.overlay_offset_y; unit: " px"; onCommitted: function(v) { hub.set("profile.overlay_offset_y", v) } }
            LabeledSlider { id: fontS; title: hub.t("Text size"); from: 10; to: 40; bound: page.prof.font_size; unit: " pt"; onCommitted: function(v) { hub.set("profile.font_size", v) } }
            LabeledSlider { id: widthS; title: hub.t("Maximum width"); from: 300; to: 1600; stepSize: 20; bound: page.prof.max_width; unit: " px"; onCommitted: function(v) { hub.set("profile.max_width", v) } }
            LabeledSlider { id: bgS; title: hub.t("Background"); from: 0; to: 100; bound: Math.round(page.prof.background_opacity * 100); unit: "%"; onCommitted: function(v) { hub.set("profile.background_opacity", v / 100) } }
            LabeledSlider { id: textS; title: hub.t("Text opacity"); from: 10; to: 100; bound: Math.round(page.prof.text_opacity * 100); unit: "%"; onCommitted: function(v) { hub.set("profile.text_opacity", v / 100) } }
            LabeledSlider { id: radiusS; title: hub.t("Corner roundness"); from: 0; to: 30; bound: page.style.corner_radius; unit: " px"; onCommitted: function(v) { hub.set("overlay.corner_radius", v) } }
            LabeledSlider {
                id: timeS
                title: hub.t("Stays on screen")
                from: 1; to: 16
                bound: page.prof.display_seconds === 0 ? 16 : page.prof.display_seconds
                display: value >= 16 ? hub.t("until the next one") : Math.round(value) + " " + hub.t("s")
                onCommitted: function(v) { hub.set("profile.display_seconds", v >= 16 ? 0 : v) }
            }
            SettingRow {
                title: hub.t("Dark outline around text")
                desc: hub.t("Easier to read over bright scenes.")
                Toggle { checked: page.style.text_outline; onToggled: function(on) { hub.set("overlay.text_outline", on) } }
            }
            SettingRow {
                title: hub.t("Fade in and out")
                Toggle { checked: page.style.animation; onToggled: function(on) { hub.set("overlay.animation", on) } }
            }
            SettingRow {
                title: hub.t("Font")
                Dropdown {
                    width: 200
                    items: hub.options("fonts")
                    current: page.style.font_family
                    onPicked: function(v) { hub.set("overlay.font_family", v) }
                }
            }
            SettingRow {
                title: hub.t("Monitor")
                Dropdown {
                    width: 200
                    items: hub.options("monitors")
                    current: page.style.monitor
                    onPicked: function(v) { hub.set("overlay.monitor", v) }
                }
            }
            SettingRow {
                title: hub.t("Warn when a game is in exclusive fullscreen")
                Toggle { checked: page.cfg.features.fullscreen_warning; onToggled: function(on) { hub.set("features.fullscreen_warning", on) } }
            }
        }
    }
}
