import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

// Title + current value + slider. Commits on release.
ColumnLayout {
    id: ls
    property string title: ""
    property string unit: ""
    property string display: Math.round(slider.value) + unit
    property alias from: slider.from
    property alias to: slider.to
    property alias stepSize: slider.stepSize
    property alias bound: slider.bound
    readonly property alias value: slider.value
    signal committed(real value)
    Layout.fillWidth: true
    spacing: 2
    RowLayout {
        Layout.fillWidth: true
        Text { text: ls.title; color: Theme.textSoft; font.pixelSize: 13; Layout.fillWidth: true }
        Text {
            text: ls.display
            color: slider.pressed ? Theme.accent : Theme.text
            font.pixelSize: 13
            font.weight: Font.DemiBold
            font.family: Theme.mono
            Behavior on color { ColorAnimation { duration: 120 } }
        }
    }
    Slide {
        id: slider
        Layout.fillWidth: true
        stepSize: 1
        snapMode: Slider.SnapAlways
        onCommitted: function(v) { ls.committed(Math.round(v)) }
    }
}
