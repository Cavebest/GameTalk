import QtQuick

// Small section label: letter-spaced capitals in English (Arabic letters must not be spaced).
Text {
    color: Theme.muted
    font.pixelSize: 11
    font.weight: Font.DemiBold
    font.letterSpacing: hub.rtl ? 0 : 1.4
    font.capitalization: hub.rtl ? Font.MixedCase : Font.AllUppercase
    elide: Text.ElideRight
}
