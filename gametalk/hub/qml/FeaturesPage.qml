import QtQuick
import QtQuick.Layouts
import "icons.js" as Icons

ScrollPage {
    id: page
    title: hub.t("Features")
    subtitle: hub.t("Switch anything on or off. A switched-off feature uses no CPU, memory or network.")
    helpTopic: "features"

    readonly property var cfg: hub.config
    readonly property var all: hub.featureList()
    property string query: ""
    readonly property var topicIcons: ({
        replay: Icons.refresh, phrases: Icons.bubble, corrections: Icons.type, pronunciation: Icons.language,
        gamepad: Icons.gamepad, teammates: Icons.users, overlay: Icons.overlay, hotkey: Icons.keyboard,
        privacy: Icons.shield, azure: Icons.cloud, general: Icons.sliders, sounds: Icons.speaker,
        quicktext: Icons.type, learning: Icons.book
    })
    function valueOf(key) {
        if (key.indexOf("teammates.") === 0) return cfg.teammates[key.split(".")[1]]
        return cfg.features[key]
    }
    function pathOf(key) { return key.indexOf(".") >= 0 ? key : "features." + key }
    readonly property var shown: {
        var q = query.trim().toLowerCase()
        return all.filter(function(f) {
            return !q || (f.label + " " + f.desc).toLowerCase().indexOf(q) >= 0
        })
    }
    readonly property int onCount: {
        var n = 0
        for (var i = 0; i < all.length; i++) if (valueOf(all[i].key)) n++
        return n
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 14
        Field {
            id: search
            Layout.preferredWidth: 340
            placeholderText: hub.t("Search features…")
            leftPadding: hub.rtl ? 12 : 38
            rightPadding: hub.rtl ? 38 : 12
            onTextChanged: page.query = text
            Icon {
                path: Icons.search
                size: 16
                color: search.activeFocus ? Theme.accent : Theme.faint
                anchors.verticalCenter: parent.verticalCenter
                x: hub.rtl ? parent.width - width - 12 : 12
            }
        }
        Item { Layout.fillWidth: true }
        Rectangle {
            implicitHeight: 30
            implicitWidth: countText.implicitWidth + 24
            radius: 15
            color: Theme.accentSoft
            border.width: 1
            border.color: Theme.accent
            Text {
                id: countText
                anchors.centerIn: parent
                text: hub.tf("{on} of {all} on", {on: page.onCount, all: page.all.length})
                color: Theme.accent
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }
        }
    }

    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 1000 ? 2 : 1
        columnSpacing: 14
        rowSpacing: 14
        Repeater {
            model: page.shown
            delegate: Card {
                id: tile
                required property var modelData
                required property int index
                readonly property bool on: !!page.valueOf(modelData.key)
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                padding: 16
                color: on ? Theme.surface : Theme.surfaceDim
                Behavior on color { ColorAnimation { duration: 200 } }
                opacity: 0
                Component.onCompleted: appear.start()
                NumberAnimation { id: appear; target: tile; property: "opacity"; from: 0; to: 1; duration: 260 + tile.index * 25 }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    Rectangle {
                        Layout.preferredWidth: 38
                        Layout.preferredHeight: 38
                        Layout.alignment: Qt.AlignTop
                        radius: 10
                        color: tile.on ? Theme.accentSoft : Theme.surface2
                        Behavior on color { ColorAnimation { duration: 200 } }
                        Icon {
                            anchors.centerIn: parent
                            path: page.topicIcons[tile.modelData.topic] || Icons.sparkle
                            size: 19
                            color: tile.on ? Theme.accent : Theme.muted
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        RowLayout {
                            spacing: 6
                            Text {
                                text: tile.modelData.label
                                color: Theme.text
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                wrapMode: Text.WordWrap
                                Layout.maximumWidth: tile.width - 170
                            }
                            HelpDot { topic: tile.modelData.topic }
                        }
                        Text {
                            text: tile.modelData.desc
                            color: Theme.muted
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                    Toggle {
                        Layout.alignment: Qt.AlignVCenter
                        checked: tile.on
                        onToggled: function(v) { hub.set(page.pathOf(tile.modelData.key), v) }
                    }
                }
            }
        }
    }

    Text {
        visible: page.shown.length === 0
        text: hub.t("No feature matches your search.")
        color: Theme.muted
        font.pixelSize: 13
    }
}
