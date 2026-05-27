// Timeline vertical com etapas (pending / active / done / error).
import QtQuick
import QtQuick.Layouts
import "."

Item {
    id: root

    // ListModel com: { name, status }  status in {pending, active, done, error}
    property var steps: []

    implicitHeight: col.implicitHeight

    ColumnLayout {
        id: col
        anchors.fill: parent
        spacing: 0

        Repeater {
            model: root.steps
            delegate: RowLayout {
                Layout.fillWidth: true
                spacing: 12

                // Coluna do indicador + linha
                Item {
                    Layout.preferredWidth: 18
                    Layout.fillHeight: true
                    implicitHeight: 44

                    // Linha de conexao
                    Rectangle {
                        visible: index < root.steps.length - 1
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: dot.bottom
                        anchors.bottom: parent.bottom
                        width: 1
                        color: modelData.status === "done"
                            ? Theme.alpha(Theme.accent, 0.5)
                            : Theme.hairline
                    }

                    Rectangle {
                        id: dot
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        anchors.topMargin: 14
                        width: 14; height: 14; radius: 7
                        color: {
                            switch (modelData.status) {
                                case "done":    return Theme.accent
                                case "active":  return Theme.bgBase
                                case "error":   return Theme.coral
                                default:        return Theme.bgBase
                            }
                        }
                        border.color: {
                            switch (modelData.status) {
                                case "done":    return Theme.accent
                                case "active":  return Theme.accent
                                case "error":   return Theme.coral
                                default:        return Theme.hairlineHi
                            }
                        }
                        border.width: 2

                        // pulse quando active
                        Rectangle {
                            visible: modelData.status === "active"
                            anchors.centerIn: parent
                            width: parent.width; height: parent.height
                            radius: width / 2
                            color: "transparent"
                            border.color: Theme.accent
                            border.width: 1
                            opacity: 0.7
                            SequentialAnimation on scale {
                                running: modelData.status === "active"
                                loops: Animation.Infinite
                                NumberAnimation { from: 1.0; to: 2.4; duration: 1300; easing.type: Easing.OutCubic }
                                PauseAnimation { duration: 60 }
                            }
                            SequentialAnimation on opacity {
                                running: modelData.status === "active"
                                loops: Animation.Infinite
                                NumberAnimation { from: 0.7; to: 0.0; duration: 1300; easing.type: Easing.OutCubic }
                                PauseAnimation { duration: 60 }
                            }
                        }

                        Text {
                            visible: modelData.status === "done"
                            anchors.centerIn: parent
                            text: "✓"
                            color: Theme.textInverse
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                    }
                }

                // Texto da etapa
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 10
                    Layout.bottomMargin: 10
                    spacing: 2

                    Text {
                        text: modelData.name
                        color: modelData.status === "pending"
                            ? Theme.textMuted : Theme.textPrimary
                        font.family: Theme.fontSans
                        font.pixelSize: Theme.sizeSm
                        font.weight: modelData.status === "active"
                            ? Font.DemiBold : Font.Normal
                    }
                    Text {
                        visible: modelData.detail !== undefined && modelData.detail !== ""
                        text: modelData.detail || ""
                        color: Theme.textMuted
                        font.family: Theme.fontMono
                        font.pixelSize: Theme.sizeMicro
                    }
                }
            }
        }
    }
}
