import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// Rotating "did you know" tips that cross-fade.
Card {
    id: tc
    property int i: 0
    readonly property var tips: [
        hub.t("Press the key a moment before you speak, and let go just after."),
        hub.t("Use Borderless or Windowed mode so the overlay shows over your game."),
        hub.t("Say the same thing often? Put it on a key in Quick phrases."),
        hub.t("For your dialect, Azure Speech or Whisper medium understand more."),
        hub.t("F10 shows your last translation again."),
        hub.t("The pronunciation helper writes the English in Arabic letters.")
    ]
    RowLayout {
        Icon { path: Icons.sparkle; size: 16; color: Theme.accent }
        Caption { text: hub.t("Tip") }
    }
    Text {
        id: tip
        Layout.fillWidth: true
        text: tc.tips[tc.i % tc.tips.length]
        color: Theme.textSoft
        font.pixelSize: 13
        wrapMode: Text.WordWrap
        Behavior on opacity { NumberAnimation { duration: 260 } }
    }
    Timer {
        interval: 7000
        running: true
        repeat: true
        onTriggered: { tip.opacity = 0; swap.start() }
    }
    Timer { id: swap; interval: 280; onTriggered: { tc.i += 1; tip.opacity = 1 } }
}
