import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// "Nothing leaves this PC" / "Only text goes to Google" — what a profile sends where.
Rectangle {
    id: tag
    property var profile
    readonly property bool local: profile.speech_provider === "whisper-local" && profile.translation_provider === "whisper-local"
    readonly property string service: profile.translation_provider === "google" ? "Google" : "Azure"
    readonly property string label: local ? hub.t("Nothing leaves this PC")
        : profile.speech_provider === "azure" ? hub.t("Voice clip goes to Azure Speech")
        : profile.speech_provider === "google" ? hub.t("Voice clip goes to Google Chirp 3")
        : hub.tf("Only the text goes to {service}", {service: service})
    implicitHeight: 26
    implicitWidth: row.implicitWidth + 20
    radius: 13
    color: local ? Theme.okSoft : Theme.warnSoft
    border.width: 1
    border.color: local ? Theme.okBorder : Theme.warnBorder
    Behavior on color { ColorAnimation { duration: 200 } }
    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 6
        Icon { path: tag.local ? Icons.lock : Icons.cloud; size: 13; stroke: 2; color: tag.local ? Theme.ok : Theme.warn }
        Text { text: tag.label; color: tag.local ? Theme.ok : Theme.warn; font.pixelSize: 11; font.weight: Font.DemiBold }
    }
}
