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
    // A janela so aparece depois que o QML terminou de carregar.
    visible: false
    width: 1280
    height: 820
    minimumWidth: 900
    minimumHeight: 600
    title: "AI Farm Agent"
    color: C.Theme.bgBase

    // 0 = tarefa, 1 = historico, 2 = sobre
    property int page: 0
    // Conversas salvas (barra lateral): clicar reabre a conversa com o contexto
    property var conversations: []
    property string currentConversation: ""

    function reloadRecents() {
        const data = JSON.parse(Bridge.loadConversations())
        conversations = data.items || []
        currentConversation = data.current || ""
    }

    function openConversation(id) {
        if (taskView.running) return
        const data = JSON.parse(Bridge.openConversation(id))
        if (!data.id) return
        page = 0
        taskView.showConversation(data)
        currentConversation = data.id
    }

    function openTask(text) {
        page = 0
        taskView.prefill(text)
    }

    Component.onCompleted: {
        reloadRecents()
    }

    Connections {
        target: Bridge
        function onHistoryChanged(json) { win.reloadRecents() }
        function onConversationsChanged(json) { win.reloadRecents() }
        function onSessionReset(json) { win.currentConversation = JSON.parse(json).session || "" }
        // Fala transcrita entra na conversa como se tivesse sido digitada
        function onVoiceCommand(json) {
            const v = JSON.parse(json)
            const t = v.text || ""
            if (!t || taskView.running) return
            win.page = 0
            taskView.start(t, v.heard || "")
        }
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
                    label: "Nova conversa"
                    icon: ""
                    active: win.page === 0 && taskView.idle && !taskView.hasConversation
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
                    visible: win.conversations.length > 0
                    Layout.topMargin: 22
                    Layout.leftMargin: 10
                    Layout.bottomMargin: 4
                    text: "Conversas"
                    color: C.Theme.textTertiary
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeSm
                    font.weight: Font.Medium
                }
                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: win.conversations
                    spacing: 1
                    boundsBehavior: Flickable.StopAtBounds
                    delegate: C.NavItem {
                        width: ListView.view.width
                        label: modelData.title
                        muted: modelData.id !== win.currentConversation
                        active: modelData.id === win.currentConversation && win.page === 0
                        onClicked: win.openConversation(modelData.id)
                        C.ToolTipHint {
                            text: modelData.title + "  ·  " + modelData.turns + (modelData.turns === 1 ? " pedido" : " pedidos")
                            shown: hovered
                        }
                        property bool hovered: false
                        HoverHandler { onHoveredChanged: parent.hovered = hovered }
                    }
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded; width: 6 }
                }
                Item { visible: win.conversations.length === 0; Layout.fillHeight: true }

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
