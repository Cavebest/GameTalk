import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "icons.js" as Icons

ApplicationWindow {
    id: win
    width: 1180
    height: 780
    minimumWidth: 940
    minimumHeight: 620
    visible: true
    color: Theme.bg
    flags: Qt.Window | Qt.FramelessWindowHint
    title: hub.t("GameTalk Translator")
    font.family: Theme.font
    font.pixelSize: 13
    LayoutMirroring.enabled: hub.rtl
    LayoutMirroring.childrenInherit: true

    property int page: startPage
    readonly property bool maximized: visibility === Window.Maximized
    readonly property var navItems: [
        {icon: Icons.home, label: hub.t("Home")},
        {icon: Icons.engine, label: hub.t("Engines")},
        {icon: Icons.toggles, label: hub.t("Features")},
        {icon: Icons.overlay, label: hub.t("Overlay")},
        {icon: Icons.users, label: hub.t("Teammates")},
        {icon: Icons.keyboard, label: hub.t("Hotkeys")},
        {icon: Icons.key, label: hub.t("Cloud keys")},
        {icon: Icons.sliders, label: hub.t("Settings")}
    ]

    Connections {
        target: hub
        function onToast(message, kind) { toast.show(message, kind) }
    }
    Shortcut { sequences: ["Ctrl+1"]; onActivated: win.page = 0 }
    Shortcut { sequences: ["Ctrl+2"]; onActivated: win.page = 1 }
    Shortcut { sequences: ["Ctrl+3"]; onActivated: win.page = 2 }
    Shortcut { sequences: ["Ctrl+4"]; onActivated: win.page = 3 }
    Shortcut { sequences: ["Ctrl+5"]; onActivated: win.page = 4 }
    Shortcut { sequences: ["Ctrl+6"]; onActivated: win.page = 5 }
    Shortcut { sequences: ["Ctrl+7"]; onActivated: win.page = 6 }
    Shortcut { sequences: ["Ctrl+8"]; onActivated: win.page = 7 }

    Item {
        id: shell
        anchors.fill: parent
        opacity: 0
        scale: 0.985
        Component.onCompleted: intro.start()
        ParallelAnimation {
            id: intro
            NumberAnimation { target: shell; property: "opacity"; to: 1; duration: 380; easing.type: Easing.OutCubic }
            NumberAnimation { target: shell; property: "scale"; to: 1; duration: 420; easing.type: Easing.OutCubic }
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // ---- title bar ---------------------------------------------------------------------
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 46
                color: Theme.chrome
                MouseArea {
                    anchors.fill: parent
                    onPressed: win.startSystemMove()
                    onDoubleClicked: win.maximized ? win.showNormal() : win.showMaximized()
                }
                RowLayout {
                    anchors { fill: parent; leftMargin: 16; rightMargin: 0 }
                    spacing: 10
                    Logo { size: 24 }
                    Text {
                        text: "GAMETALK"
                        color: Theme.text
                        font.pixelSize: 13
                        font.weight: Font.Black
                        font.letterSpacing: 2.2
                    }
                    Text { text: "v" + hub.version; color: Theme.faint; font.pixelSize: 11 }
                    Item { Layout.fillWidth: true }
                    StatusPill {}
                    Item { width: 8 }
                    WinButton { icon: Icons.minus; onClicked: win.showMinimized() }
                    WinButton { icon: Icons.maximize; onClicked: win.maximized ? win.showNormal() : win.showMaximized() }
                    WinButton { icon: Icons.close; danger: true; onClicked: win.close() }
                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: Theme.border }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                // ---- sidebar -------------------------------------------------------------------
                Rectangle {
                    Layout.preferredWidth: 216
                    Layout.fillHeight: true
                    color: Theme.chrome
                    Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: Theme.border }

                    Rectangle {  // sliding selection
                        id: indicator
                        x: 10
                        width: parent.width - 21
                        height: 42
                        y: nav.y + win.page * 46
                        radius: 9
                        color: Theme.surface2
                        Behavior on y { NumberAnimation { duration: 340; easing.type: Easing.OutBack; easing.overshoot: 1.1 } }
                        Rectangle {
                            width: 3
                            height: 20
                            radius: 2
                            anchors.verticalCenter: parent.verticalCenter
                            x: 0
                            color: Theme.accent
                        }
                    }

                    Column {
                        id: nav
                        x: 10
                        y: 16
                        width: parent.width - 21
                        spacing: 4
                        Repeater {
                            model: win.navItems
                            delegate: Item {
                                id: navItem
                                required property var modelData
                                required property int index
                                readonly property bool current: win.page === index
                                width: nav.width
                                height: 42
                                RowLayout {
                                    anchors { fill: parent; leftMargin: 16; rightMargin: 12 }
                                    spacing: 12
                                    Icon {
                                        path: navItem.modelData.icon
                                        size: 19
                                        color: navItem.current ? Theme.accent : (nm.containsMouse ? Theme.text : Theme.muted)
                                    }
                                    Text {
                                        text: navItem.modelData.label
                                        color: navItem.current ? Theme.text : (nm.containsMouse ? Theme.text : Theme.muted)
                                        font.pixelSize: 13
                                        font.weight: navItem.current ? Font.DemiBold : Font.Medium
                                        Layout.fillWidth: true
                                        Behavior on color { ColorAnimation { duration: 150 } }
                                    }
                                    Rectangle {  // warning dot on Cloud keys when a chosen service lacks a key
                                        visible: navItem.index === 6 && win.missingKey
                                        width: 7; height: 7; radius: 4
                                        color: Theme.warn
                                    }
                                }
                                MouseArea {
                                    id: nm
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: win.page = navItem.index
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 12 }
                        spacing: 8
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 40
                            radius: 9
                            color: lm.containsMouse ? Theme.surface2 : "transparent"
                            Behavior on color { ColorAnimation { duration: 150 } }
                            RowLayout {
                                anchors { fill: parent; leftMargin: 14; rightMargin: 12 }
                                spacing: 10
                                Icon { path: Icons.language; size: 17; color: Theme.muted }
                                Text { text: hub.rtl ? "English" : "العربية"; color: Theme.textSoft; font.pixelSize: 13; Layout.fillWidth: true }
                            }
                            MouseArea {
                                id: lm
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: hub.setLanguage(hub.rtl ? "en" : "ar")
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 40
                            radius: 9
                            color: hm.containsMouse ? Theme.surface2 : "transparent"
                            Behavior on color { ColorAnimation { duration: 150 } }
                            RowLayout {
                                anchors { fill: parent; leftMargin: 14; rightMargin: 12 }
                                spacing: 10
                                Icon { path: Icons.help; size: 17; color: Theme.muted }
                                Text { text: hub.t("Help"); color: Theme.textSoft; font.pixelSize: 13; Layout.fillWidth: true }
                            }
                            MouseArea {
                                id: hm
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: hub.openHelp("start")
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignHCenter
                            text: "by Shkour Bashtawi"
                            color: Theme.faint
                            font.pixelSize: 11
                        }
                    }
                }

                // ---- pages ---------------------------------------------------------------------
                Item {
                    id: pages
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    PageHost { index: 0; source: "HomePage.qml" }
                    PageHost { index: 1; source: "EnginesPage.qml" }
                    PageHost { index: 2; source: "FeaturesPage.qml" }
                    PageHost { index: 3; source: "OverlayPage.qml" }
                    PageHost { index: 4; source: "TeammatesPage.qml" }
                    PageHost { index: 5; source: "HotkeysPage.qml" }
                    PageHost { index: 6; source: "KeysPage.qml" }
                    PageHost { index: 7; source: "MorePage.qml" }
                    Toast { id: toast }
                }
            }
        }

        Rectangle {  // hairline window border (frameless window)
            anchors.fill: parent
            color: "transparent"
            border.width: win.maximized ? 0 : 1
            border.color: Theme.borderHover
        }
    }

    readonly property bool missingKey: {
        var c = hub.config, p = c.profile
        return (p.speech_provider === "azure" && !(c.azure.speech_key && c.azure.speech_region))
            || (p.translation_provider === "azure" && !c.azure.translator_key)
            || (p.translation_provider === "google" && !c.google.api_key)
    }

    // A page slides in from the side it lives on, and fades.
    component PageHost: Item {
        id: host
        property int index: 0
        property string source: ""
        property bool visited: win.page === index
        readonly property bool current: win.page === index
        onCurrentChanged: if (current) visited = true
        anchors.fill: parent
        opacity: current ? 1 : 0
        visible: opacity > 0.01
        Behavior on opacity { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
        transform: Translate {
            x: host.current ? 0 : (host.index < win.page ? -28 : 28) * (hub.rtl ? -1 : 1)
            Behavior on x { NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }
        }
        Loader {
            id: loader
            anchors.fill: parent
            active: host.visited
            source: host.source
        }
        Connections {
            target: loader.item
            ignoreUnknownSignals: true
            function onNavigate(p) { win.page = p }
        }
    }

    component WinButton: Rectangle {
        id: wb
        property string icon: ""
        property bool danger: false
        signal clicked()
        Layout.preferredWidth: 46
        Layout.fillHeight: true
        color: wm.containsMouse ? (danger ? "#e81123" : Theme.surface2) : "transparent"
        Behavior on color { ColorAnimation { duration: 120 } }
        Icon {
            anchors.centerIn: parent
            path: wb.icon
            size: 15
            stroke: 1.5
            color: wm.containsMouse ? "#ffffff" : Theme.muted
        }
        MouseArea { id: wm; anchors.fill: parent; hoverEnabled: true; onClicked: wb.clicked() }
    }

    component StatusPill: Rectangle {
        id: pill
        readonly property var st: hub.stats
        readonly property string phase: !hub.running ? (hub.starting ? "starting" : "off")
            : st.state === "disabled" ? "off" : st.loading ? "starting" : (st.phase || "idle")
        readonly property color tone: phase === "off" ? Theme.faint : phase === "recording" ? Theme.danger
            : phase === "idle" ? Theme.ok : Theme.accent
        implicitHeight: 26
        implicitWidth: pr.implicitWidth + 22
        radius: 13
        color: Qt.rgba(tone.r, tone.g, tone.b, 0.12)
        border.width: 1
        border.color: Qt.rgba(tone.r, tone.g, tone.b, 0.35)
        Behavior on color { ColorAnimation { duration: 250 } }
        RowLayout {
            id: pr
            anchors.centerIn: parent
            spacing: 7
            Rectangle {
                width: 7; height: 7; radius: 4
                color: pill.tone
                SequentialAnimation on opacity {
                    running: pill.phase !== "off"
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.3; duration: pill.phase === "recording" ? 300 : 800 }
                    NumberAnimation { to: 1; duration: pill.phase === "recording" ? 300 : 800 }
                }
            }
            Text {
                text: pill.phase === "off" ? hub.t("Off")
                    : pill.phase === "starting" ? hub.t("Starting…")
                    : pill.phase === "recording" ? hub.t("Listening…")
                    : pill.phase === "processing" ? hub.t("Translating…")
                    : hub.tf("Ready · {key}", {key: pill.st.hotkey || hub.config.profile.hotkey})
                color: pill.tone
                font.pixelSize: 11
                font.weight: Font.DemiBold
            }
        }
    }

    // ---- resize handles (the window has no system frame) -----------------------------------------
    Repeater {
        model: win.maximized ? [] : [
            {e: Qt.LeftEdge, c: Qt.SizeHorCursor}, {e: Qt.RightEdge, c: Qt.SizeHorCursor},
            {e: Qt.TopEdge, c: Qt.SizeVerCursor}, {e: Qt.BottomEdge, c: Qt.SizeVerCursor},
            {e: Qt.TopEdge | Qt.LeftEdge, c: Qt.SizeFDiagCursor}, {e: Qt.BottomEdge | Qt.RightEdge, c: Qt.SizeFDiagCursor},
            {e: Qt.TopEdge | Qt.RightEdge, c: Qt.SizeBDiagCursor}, {e: Qt.BottomEdge | Qt.LeftEdge, c: Qt.SizeBDiagCursor}
        ]
        delegate: MouseArea {
            required property var modelData
            readonly property bool l: (modelData.e & Qt.LeftEdge) !== 0
            readonly property bool r: (modelData.e & Qt.RightEdge) !== 0
            readonly property bool t: (modelData.e & Qt.TopEdge) !== 0
            readonly property bool b: (modelData.e & Qt.BottomEdge) !== 0
            LayoutMirroring.enabled: false
            x: r ? win.width - width : 0
            y: b ? win.height - height : 0
            width: (l || r) ? ((t || b) ? 12 : 6) : win.width
            height: (t || b) ? ((l || r) ? 12 : 6) : win.height
            cursorShape: modelData.c
            onPressed: win.startSystemResize(modelData.e)
        }
    }
}
