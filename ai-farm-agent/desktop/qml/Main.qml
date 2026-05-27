// Janela raiz — moldura nativa do sistema (Windows/Linux/Mac padrao),
// estetica Claude/Lanes.sh: fundo preto profundo, halos teal/roxo sutis,
// 3 abas (Command Center / Activity / About).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components" as C
import "views" as V

ApplicationWindow {
    id: win
    visible: true
    // Tamanho "restored" — usado quando o usuario sai do maximizado.
    // Adapta a qualquer monitor: notebook 1366x768 ou desktop 4K.
    width: 1280
    height: 800
    minimumWidth: 980
    minimumHeight: 600
    title: "AI Farm Agent"
    color: C.Theme.bgBase

    // Abre MAXIMIZADA por padrao — funciona em qualquer resolucao.
    // O Windows/Linux respeita a area util (descontando taskbar/dock).
    visibility: Window.Maximized

    Component.onCompleted: {
        // Calcula tamanho/posicao "restored" sensatos para o monitor atual:
        // 80% da tela, centralizado. Sera usado quando o usuario sair do
        // maximizado (clicando no botao restaurar).
        const s = Screen
        if (s && s.width > 0 && s.height > 0) {
            const restoredW = Math.min(1600, Math.round(s.width  * 0.80))
            const restoredH = Math.min(1000, Math.round(s.height * 0.80))
            width  = Math.max(minimumWidth,  restoredW)
            height = Math.max(minimumHeight, restoredH)
            x = Math.max(0, Math.round((s.width  - width)  / 2))
            y = Math.max(0, Math.round((s.height - height) / 2) - 20)
        }
        // Garante que ABRE maximizada (mesmo se algum estado quiser normal)
        if (visibility !== Window.Maximized && visibility !== Window.FullScreen) {
            showMaximized()
        }
    }

    property int stage: 0
    property string view: "command"

    // ── Ambient gradient: halos teal e roxo muito sutis ──
    // Tamanhos PROPORCIONAIS a janela, com clip para nao vazar.
    Item {
        anchors.fill: parent
        clip: true
        z: -1

        Rectangle {
            readonly property real diag: Math.min(parent.width, parent.height) * 0.85
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.leftMargin: -diag * 0.4
            anchors.bottomMargin: -diag * 0.35
            width: diag; height: diag
            radius: diag / 2
            opacity: 0.07
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#2dd4bf" }
                GradientStop { position: 1.0; color: "transparent" }
            }
        }
        Rectangle {
            readonly property real diag: Math.min(parent.width, parent.height) * 0.75
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.rightMargin: -diag * 0.35
            anchors.topMargin: -diag * 0.32
            width: diag; height: diag
            radius: diag / 2
            opacity: 0.06
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#a78bfa" }
                GradientStop { position: 1.0; color: "transparent" }
            }
        }
    }

    Loader {
        id: stageLoader
        anchors.fill: parent
        sourceComponent: stage === 0 ? splashComp : appComp
        clip: true
    }

    Component {
        id: splashComp
        Splash {
            anchors.fill: parent
            onEnterRequested: transitionToApp.start()
        }
    }

    NumberAnimation {
        id: transitionToApp
        target: stageLoader; property: "opacity"
        from: 1; to: 0; duration: 280
        onFinished: { win.stage = 1; stageLoader.opacity = 1 }
    }

    // ─── APP ────────────────────────────────────────────────────────
    Component {
        id: appComp
        Item {
            anchors.fill: parent

            // CABECALHO interno (nao e title bar do SO — esse e nativo)
            Rectangle {
                id: header
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: 52
                color: "transparent"

                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: 1
                    color: Qt.rgba(1, 1, 1, 0.05)
                }

                // Logo + nome a esquerda
                RowLayout {
                    anchors.left: parent.left
                    anchors.leftMargin: 24
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    C.HexLogo { sizePx: 18; tone: C.Theme.accent }
                    Text {
                        text: "AI Farm Agent"
                        color: C.Theme.textPrimary
                        font.family: C.Theme.fontSans
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        font.letterSpacing: -0.2
                    }
                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 16
                        color: C.Theme.hairline
                    }
                    Text {
                        text: "v2.0"
                        color: C.Theme.textMuted
                        font.family: C.Theme.fontMono
                        font.pixelSize: 11
                        font.letterSpacing: 0.4
                    }
                }

                // Status • Online a direita
                RowLayout {
                    anchors.right: parent.right
                    anchors.rightMargin: 24
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8
                    Rectangle {
                        width: 7; height: 7; radius: 3.5
                        color: C.Theme.accent
                        SequentialAnimation on opacity {
                            running: true; loops: Animation.Infinite
                            NumberAnimation { from: 1.0; to: 0.4; duration: 1600; easing.type: Easing.InOutSine }
                            NumberAnimation { from: 0.4; to: 1.0; duration: 1600; easing.type: Easing.InOutSine }
                        }
                    }
                    Text {
                        text: "Online"
                        color: C.Theme.accent
                        font.family: C.Theme.fontMono
                        font.pixelSize: 11
                        font.letterSpacing: 0.6
                        font.weight: Font.Medium
                    }
                }
            }

            // SIDEBAR
            Item {
                id: sidebar
                anchors.top: header.bottom
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                width: 200

                Rectangle {
                    anchors.right: parent.right
                    width: 1; height: parent.height
                    color: Qt.rgba(1, 1, 1, 0.05)
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    anchors.topMargin: 20
                    spacing: 4

                    Text {
                        Layout.leftMargin: 10
                        text: "Menu"
                        color: C.Theme.textMuted
                        font.family: C.Theme.fontMono
                        font.pixelSize: 9
                        font.letterSpacing: 1.5
                    }

                    Item { Layout.preferredHeight: 8 }

                    C.SidebarItem {
                        Layout.fillWidth: true
                        label: "Command Center"; glyph: "⌂"
                        active: win.view === "command"
                        onClicked: win.view = "command"
                    }
                    C.SidebarItem {
                        Layout.fillWidth: true
                        label: "Activity"; glyph: "≡"
                        active: win.view === "activity"
                        onClicked: win.view = "activity"
                    }
                    C.SidebarItem {
                        Layout.fillWidth: true
                        label: "About"; glyph: "ⓘ"
                        active: win.view === "about"
                        onClicked: win.view = "about"
                    }

                    Item { Layout.fillHeight: true }

                    // Rodape: avatar + ognistie
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 10
                        Layout.bottomMargin: 6
                        spacing: 8

                        Rectangle {
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                            radius: 11
                            color: C.Theme.textPrimary
                            Text {
                                anchors.centerIn: parent
                                text: ""
                                color: C.Theme.bgBase
                                font.family: "Segoe Fluent Icons, Segoe MDL2 Assets"
                                font.pixelSize: 13
                            }
                        }
                        Text {
                            text: "ognistie"
                            color: C.Theme.textSecondary
                            font.family: C.Theme.fontMono
                            font.pixelSize: 11
                            Layout.alignment: Qt.AlignVCenter
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://github.com/ognistie")
                            }
                        }
                    }
                }
            }

            // CONTEUDO
            Item {
                anchors.top: header.bottom
                anchors.bottom: parent.bottom
                anchors.left: sidebar.right
                anchors.right: parent.right

                Loader {
                    id: viewLoader
                    anchors.fill: parent
                    sourceComponent: {
                        switch (win.view) {
                            case "command":   return commandComp
                            case "activity":  return activityComp
                            case "about":     return aboutComp
                        }
                        return commandComp
                    }
                    onSourceComponentChanged: viewFade.restart()
                    opacity: 0
                    NumberAnimation on opacity {
                        id: viewFade
                        from: 0; to: 1; duration: 220; easing.type: Easing.OutCubic
                    }
                }
            }
        }
    }

    Component { id: commandComp;   V.CommandCenterView {} }
    Component { id: activityComp;  V.ActivityView {} }
    Component { id: aboutComp;     V.AboutView {} }
}
