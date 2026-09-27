import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

// Editable list of pairs (key → sentence, wrong word → right word). Rows slide in; saving
// happens on every finished edit. The list reloads when you switch profile.
ColumnLayout {
    id: pl
    property var source: []          // [{a, b}] from the settings
    property string reloadKey: ""    // e.g. the active profile name
    property string aHint: ""
    property string bHint: ""
    property var keyOptions: null    // [{value,label}] -> the first column is a key picker
    property bool rtlText: false     // Arabic words in both columns
    property string addText: hub.t("Add")
    signal save(var rows)
    property var rows: []
    Layout.fillWidth: true
    spacing: 8

    function load() { rows = (source || []).map(function(r) { return {a: r.a, b: r.b} }) }
    onReloadKeyChanged: load()
    Component.onCompleted: load()
    function commit() {
        save(rows.filter(function(r) { return (r.a || "").trim() || (r.b || "").trim() }))
    }
    function update(i, field, value) {
        if (rows[i][field] === value) return
        var copy = rows.slice()
        copy[i] = {a: copy[i].a, b: copy[i].b}
        copy[i][field] = value
        rows = copy
        commit()
    }
    function remove(i) {
        var copy = rows.slice()
        copy.splice(i, 1)
        rows = copy
        commit()
    }
    function add(a, b) {
        rows = rows.concat([{a: a || "", b: b || ""}])
        if (a || b) commit()
    }

    Repeater {
        model: pl.rows
        delegate: RowLayout {
            id: row
            required property var modelData
            required property int index
            Layout.fillWidth: true
            spacing: 8
            opacity: 0
            Component.onCompleted: fadeIn.start()
            NumberAnimation { id: fadeIn; target: row; property: "opacity"; to: 1; duration: 220 }

            Dropdown {
                visible: pl.keyOptions !== null
                Layout.preferredWidth: 150
                items: pl.keyOptions || []
                current: row.modelData.a
                onPicked: function(v) { pl.update(row.index, "a", v) }
            }
            Field {
                visible: pl.keyOptions === null
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: row.modelData.a
                placeholderText: pl.aHint
                horizontalAlignment: pl.rtlText ? Text.AlignRight : Text.AlignLeft
                onEditingFinished: pl.update(row.index, "a", text.trim())
            }
            Icon {
                path: hub.rtl ? Icons.chevronRight : Icons.chevronRight
                rotation: hub.rtl ? 180 : 0
                size: 16
                color: Theme.faint
            }
            Field {
                Layout.fillWidth: true
                Layout.preferredWidth: pl.keyOptions === null ? 1 : 3
                text: row.modelData.b
                placeholderText: pl.bHint
                horizontalAlignment: pl.rtlText ? Text.AlignRight : Text.AlignLeft
                onEditingFinished: pl.update(row.index, "b", text.trim())
            }
            Rectangle {
                width: 34; height: 34; radius: 8
                color: dm.containsMouse ? Theme.dangerSoft : "transparent"
                Behavior on color { ColorAnimation { duration: 120 } }
                Icon { anchors.centerIn: parent; path: Icons.trash; size: 16; color: dm.containsMouse ? Theme.danger : Theme.faint }
                MouseArea { id: dm; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: pl.remove(row.index) }
            }
        }
    }
    Btn {
        text: pl.addText
        icon: Icons.plus
        small: true
        kind: "subtle"
        onClicked: pl.add("", "")
    }
}
