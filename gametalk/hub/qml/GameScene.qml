import QtQuick

// A mock game frame (sunset city + HUD) with the overlay drawn exactly as configured.
// Sizes are scaled from a 1280-px-wide screen (bigger than life, so it stays readable). Never mirrored: it's a picture of the screen.
Rectangle {
    id: scene
    property string position: "top-center"
    property int offsetX: 0
    property int offsetY: 48
    property real fontSize: 18
    property real maxWidth: 640
    property real bgOpacity: 0.72
    property real textOpacity: 1
    property real radiusPx: 12
    property color accent: "#ff5a1f"
    property color textColor: "#f5f7fa"
    property color bgColor: "#0c0e14"
    property bool outline: false
    property bool showPron: false
    readonly property real k: width / 1280  // a 1280-px-wide screen keeps the preview readable
    LayoutMirroring.enabled: false
    LayoutMirroring.childrenInherit: true
    radius: 10
    clip: true
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#1b2a4a" }
        GradientStop { position: 0.5; color: "#c77a4a" }
        GradientStop { position: 0.56; color: "#3a3026" }
        GradientStop { position: 1.0; color: "#14100c" }
    }

    Rectangle {  // sun
        width: scene.width * 0.12; height: width; radius: width / 2
        x: scene.width * 0.66; y: scene.height * 0.22
        color: "#ffd9a8"; opacity: 0.55
    }
    Repeater {  // skyline
        model: [0.07, 0.19, 0.12, 0.27, 0.16, 0.33, 0.21, 0.13, 0.25, 0.18, 0.3, 0.11, 0.22, 0.15]
        delegate: Rectangle {
            required property real modelData
            required property int index
            width: scene.width / 14 - 3
            x: index * scene.width / 14
            height: scene.height * modelData * 1.25
            y: scene.height * 0.56 - height
            color: index % 3 === 0 ? "#1d1a22" : "#221c24"
        }
    }
    Repeater {  // ground lines
        model: 8
        delegate: Rectangle {
            required property int index
            width: scene.width
            height: 1
            y: scene.height * 0.56 + scene.height * 0.44 * Math.pow(index / 8, 1.6)
            color: "#ffffff"
            opacity: 0.06
        }
    }
    Item {  // crosshair
        anchors.centerIn: parent
        width: 22; height: 22
        Rectangle { x: 0; y: 10; width: 7; height: 2; color: "#7dffb0" }
        Rectangle { x: 15; y: 10; width: 7; height: 2; color: "#7dffb0" }
        Rectangle { x: 10; y: 0; width: 2; height: 7; color: "#7dffb0" }
        Rectangle { x: 10; y: 15; width: 2; height: 7; color: "#7dffb0" }
    }
    Rectangle {  // health bar
        x: scene.width * 0.02; y: scene.height - height - scene.height * 0.04
        width: scene.width * 0.16; height: scene.height * 0.035; radius: 3
        color: "#66000000"
        Rectangle { x: 3; y: 3; width: parent.width * 0.7; height: parent.height - 6; radius: 2; color: "#22c55e" }
    }
    Rectangle {  // minimap
        width: scene.height * 0.2; height: width; radius: width / 2
        x: scene.width - width - scene.width * 0.02; y: scene.height * 0.04
        color: "#77000000"; border.width: 1; border.color: "#55ffffff"
        Rectangle { anchors.centerIn: parent; width: 5; height: 5; radius: 3; color: "#38bdf8" }
    }

    // ---- the overlay bubble ---------------------------------------------------------------
    Rectangle {
        id: bubble
        readonly property string hpos: scene.position.split("-").length > 1 ? scene.position.split("-")[1] : "center"
        readonly property string vpos: scene.position === "center" ? "middle" : scene.position.split("-")[0]
        readonly property real pad: 16 * scene.k
        width: Math.min(scene.maxWidth * scene.k, Math.max(main.implicitWidth, pron.visible ? pron.implicitWidth : 0) + pad * 2 + 6)
        height: col.implicitHeight + pad * 1.4
        x: hpos === "left" ? 24 * scene.k + scene.offsetX * scene.k
         : hpos === "right" ? scene.width - width - 24 * scene.k + scene.offsetX * scene.k
         : (scene.width - width) / 2 + scene.offsetX * scene.k
        y: vpos === "top" ? scene.offsetY * scene.k
         : vpos === "bottom" ? scene.height - height - scene.offsetY * scene.k
         : (scene.height - height) / 2 + scene.offsetY * scene.k
        radius: scene.radiusPx * scene.k
        color: Qt.rgba(scene.bgColor.r, scene.bgColor.g, scene.bgColor.b, scene.bgOpacity)
        Behavior on x { NumberAnimation { duration: 380; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: 380; easing.type: Easing.OutCubic } }
        Behavior on width { NumberAnimation { duration: 200 } }

        Rectangle {
            x: bubble.pad * 0.45
            anchors.verticalCenter: parent.verticalCenter
            width: Math.max(2, 3 * scene.k * 1.4)
            height: parent.height - bubble.pad
            radius: 1
            color: scene.accent
        }
        Column {
            id: col
            x: bubble.pad + 4
            y: bubble.pad * 0.7
            width: bubble.width - bubble.pad * 2
            spacing: 2
            Text {
                id: main
                width: Math.min(implicitWidth, col.width)
                text: "Enemy on the left, cover me!"
                wrapMode: Text.WordWrap
                color: Qt.rgba(scene.textColor.r, scene.textColor.g, scene.textColor.b, scene.textOpacity)
                font.pixelSize: Math.max(7, scene.fontSize * 1.333 * scene.k)
                font.weight: Font.DemiBold
                style: scene.outline ? Text.Outline : Text.Normal
                styleColor: "#000000"
            }
            Text {
                id: pron
                visible: scene.showPron
                width: col.width
                text: "إنمي أون ذا ليفت، كافر مي!"
                horizontalAlignment: Text.AlignRight
                color: Qt.rgba(scene.textColor.r, scene.textColor.g, scene.textColor.b, scene.textOpacity * 0.72)
                font.pixelSize: Math.max(6, scene.fontSize * 0.72 * 1.333 * scene.k)
            }
        }
    }
}
