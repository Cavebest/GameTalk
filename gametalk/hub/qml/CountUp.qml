import QtQuick

// A number that rolls to its new value.
Text {
    id: cu
    property real value: 0
    property int decimals: 0
    property real shown: 0
    property bool empty: false  // no data yet: show a dash, not a misleading zero
    text: empty ? "—" : shown.toFixed(decimals)
    color: Theme.text
    font.weight: Font.Bold
    font.family: Theme.font
    Behavior on shown { NumberAnimation { duration: 900; easing.type: Easing.OutCubic } }
    Component.onCompleted: shown = Qt.binding(function() { return value })
}
