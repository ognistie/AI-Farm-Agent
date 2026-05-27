// Card com efeito "vidro fume" — semi-transparente, hairline tenue,
// highlight 1px no topo (luz vinda de cima) e sombra suave embaixo.
// Estetica Claude/Lanes.sh: profundidade sutil sem barulho visual.
import QtQuick
import QtQuick.Effects
import "."

Rectangle {
    id: root

    property string title: ""
    property string subtitle: ""
    property bool padded: false
    property alias contentItem: contentArea
    default property alias children: contentArea.data

    color: Qt.rgba(0.071, 0.075, 0.086, 0.78)   // bgSurface @ 78%
    radius: Theme.rLg
    border.color: Theme.alpha(Qt.rgba(1,1,1,1), 0.05)
    border.width: 1

    // Highlight 1px no topo — luz vinda de cima
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 1
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        height: 1
        radius: parent.radius
        color: Qt.rgba(1, 1, 1, 0.04)
    }

    // Sombra externa muito suave
    layer.enabled: true
    layer.effect: MultiEffect {
        shadowEnabled: true
        shadowColor: Qt.rgba(0, 0, 0, 0.55)
        shadowBlur: 0.7
        shadowVerticalOffset: 10
        shadowHorizontalOffset: 0
        shadowOpacity: 0.45
    }

    Item {
        id: headerArea
        visible: root.title !== "" || root.subtitle !== ""
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: visible ? 52 : 0

        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: Theme.spXl
            anchors.rightMargin: Theme.spXl
            spacing: 2

            Text {
                visible: root.title !== ""
                text: root.title
                color: Theme.textPrimary
                font.family: Theme.fontSans
                font.pixelSize: Theme.sizeMd
                font.weight: Font.Medium
                font.letterSpacing: -0.2
            }
            Text {
                visible: root.subtitle !== ""
                text: root.subtitle
                color: Theme.textMuted
                font.family: Theme.fontSans
                font.pixelSize: Theme.sizeXs
            }
        }

        Rectangle {
            visible: root.title !== "" || root.subtitle !== ""
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            height: 1
            color: Theme.alpha(Qt.rgba(1,1,1,1), 0.04)
        }
    }

    Item {
        id: contentArea
        anchors.top: headerArea.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: root.padded ? Theme.spXl : 0
    }
}
