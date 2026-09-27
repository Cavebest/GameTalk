import QtQuick

// Big English sentence that types itself in whenever a new translation arrives.
Text {
    id: tt
    property string full: ""
    property string placeholder: ""
    property int shownChars: full.length
    text: full ? full.substring(0, shownChars) + (shownChars < full.length ? "▍" : "") : placeholder
    color: full ? Theme.text : Theme.faint
    font.pixelSize: full ? 24 : 15
    font.weight: full ? Font.DemiBold : Font.Normal
    wrapMode: Text.WordWrap
    horizontalAlignment: Text.AlignLeft
    LayoutMirroring.enabled: false  // English reads left-to-right even in the Arabic UI
    onFullChanged: { shownChars = 0; typing.restart() }

    Timer {
        id: typing
        interval: 22
        repeat: true
        onTriggered: {
            if (tt.shownChars >= tt.full.length) { stop(); return }
            tt.shownChars += 1
        }
    }
}
