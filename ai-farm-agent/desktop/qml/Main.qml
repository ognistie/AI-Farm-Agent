// Janela raiz: sidebar (navegacao + recentes) e area de conteudo.
// As telas ficam num StackLayout para manter o estado ao trocar de aba —
// uma tarefa em execucao continua visivel ao voltar para ela.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components" as C
import "views" as V

ApplicationWindow {
    id: win
    visible: true
    width: 1280
    height: 820
    minimumWidth: 900
    minimumHeight: 600
    title: "AI Farm Agent"
    color: C.Theme.bgBase

    // 0 = tarefa, 1 = historico, 2 = sobre
    property int page: 0
    property var recents: []

    function reloadRecents() {
        const data = JSON.parse(Bridge.loadHistory())
        const seen = []
        const out = []
        for (const it of (data.items || [])) {
            const t = (it.task || "").trim()
            if (!t || seen.indexOf(t) >= 0) continue
            seen.push(t)
            out.push(t)
            if (out.length >= 8) break
        }
        recents = out
    }

    function openTask(text) {
        page = 0
        taskView.prefill(text)
    }

    Component.onCompleted: {
        const s = Screen
        if (s && s.desktopAvailableWidth > 0) {
            width = Math.max(minimumWidth, Math.min(1440, Math.round(s.desktopAvailableWidth * 0.85)))
            height = Math.max(minimumHeight, Math.min(960, Math.round(s.desktopAvailableHeight * 0.88)))
            x = Math.round((s.desktopAvailableWidth - width) / 2)
            y = Math.round((s.desktopAvailableHeight - height) / 2)
        }
        reloadRecents()
    }

    Connections {
        target: Bridge
        function onHistoryChanged(json) { win.reloadRecents() }
    }

    Shortcut { sequence: "Ctrl+N"; onActivated: { win.page = 0; taskView.newTask() } }
    Shortcut { sequence: "Ctrl+H"; onActivated: win.page = 1 }
    Shortcut { sequence: "Esc"; enabled: taskView.running; onActivated: Bridge.forceStop() }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ═══ Sidebar ════════════════════════════════════════════════
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 248
            color: C.Theme.bgSidebar

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                anchors.topMargin: 16
                spacing: 2

                // Marca
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.bottomMargin: 14
                    spacing: 10
                    Rectangle {
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 26
                        radius: 7
                        color: C.Theme.primary
                        C.HexLogo {
                            anchors.centerIn: parent
                            sizePx: 15
                            tone: C.Theme.textInverse
                        }
                    }
                    Text {
                        text: "AI Farm Agent"
                        color: C.Theme.textPrimary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeMd + 1
                        font.weight: Font.DemiBold
                    }
                }

                C.NavItem {
                    Layout.fillWidth: true
                    label: "Nova tarefa"
                    icon: ""
                    active: win.page === 0 && taskView.idle
                    onClicked: { win.page = 0; taskView.newTask() }
                }
                C.NavItem {
                    Layout.fillWidth: true
                    visible: !taskView.idle
                    label: taskView.running ? "Em execução" : "Tarefa atual"
                    icon: taskView.running ? "" : ""
                    active: win.page === 0 && !taskView.idle
                    onClicked: win.page = 0
                }
                C.NavItem {
                    Layout.fillWidth: true
                    label: "Histórico"
                    icon: ""
                    active: win.page === 1
                    onClicked: win.page = 1
                }
                C.NavItem {
                    Layout.fillWidth: true
                    label: "Sobre"
                    icon: ""
                    active: win.page === 2
                    onClicked: win.page = 2
                }

                // Recentes
                Text {
                    visible: win.recents.length > 0
                    Layout.topMargin: 22
                    Layout.leftMargin: 10
                    Layout.bottomMargin: 4
                    text: "Recentes"
                    color: C.Theme.textTertiary
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeSm
                    font.weight: Font.Medium
                }
                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: win.recents
                    spacing: 1
                    boundsBehavior: Flickable.StopAtBounds
                    delegate: C.NavItem {
                        width: ListView.view.width
                        label: modelData
                        muted: true
                        onClicked: win.openTask(modelData)
                        C.ToolTipHint { text: modelData; shown: hovered && modelData.length > 34 }
                        property bool hovered: false
                        HoverHandler { onHoveredChanged: parent.hovered = hovered }
                    }
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded; width: 6 }
                }
                Item { visible: win.recents.length === 0; Layout.fillHeight: true }

                // Rodape: modelo em uso
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: C.Theme.hairline
                    Layout.bottomMargin: 8
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 10
                    Layout.bottomMargin: 4
                    spacing: 8
                    Rectangle {
                        Layout.preferredWidth: 6
                        Layout.preferredHeight: 6
                        radius: 3
                        color: taskView.running ? C.Theme.warning : C.Theme.success
                    }
                    Text {
                        Layout.fillWidth: true
                        text: taskView.running ? "Executando..." : "Pronto  ·  Claude Sonnet 5"
                        color: C.Theme.textTertiary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeSm
                        elide: Text.ElideRight
                    }
                }
            }

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: C.Theme.hairline
            }
        }

        // ═══ Conteudo ═══════════════════════════════════════════════
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: win.page

            V.TaskView { id: taskView; objectName: "taskView" }
            V.HistoryView { onReuseRequested: (t) => win.openTask(t) }
            V.AboutView {}
        }
    }
}
