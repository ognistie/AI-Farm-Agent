// Historico de execucoes (desktop/data/history.jsonl). Busca, status,
// duracao e custo real. Clique numa linha para reusar o pedido.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Item {
    id: root

    signal reuseRequested(string task)

    property var items: []
    property var stats: ({ total: 0, success_rate: 0, total_cost_usd: 0 })
    property string query: ""

    readonly property var filtered: {
        const q = query.trim().toLowerCase()
        if (!q) return items
        return items.filter(it => (it.task || "").toLowerCase().indexOf(q) >= 0)
    }

    function reload() {
        const data = JSON.parse(Bridge.loadHistory())
        items = data.items || []
        stats = data.stats || stats
    }

    function fmtWhen(iso) {
        if (!iso) return ""
        const d = new Date(iso)
        const today = new Date()
        const sameDay = d.toDateString() === today.toDateString()
        const time = d.toLocaleTimeString(Qt.locale("pt_BR"), "HH:mm")
        return sameDay ? "Hoje, " + time : d.toLocaleDateString(Qt.locale("pt_BR"), "dd/MM") + ", " + time
    }
    function fmtDuration(ms) {
        const s = Math.round((ms || 0) / 1000)
        return s < 60 ? s + "s" : Math.floor(s / 60) + "min " + (s % 60) + "s"
    }
    function fmtCost(v) { return "US$ " + (v || 0).toFixed(4).replace(".", ",") }
    function agentsOf(it) {
        const seen = []
        for (const s of (it.subtasks || [])) {
            const l = C.Theme.agentLabel(s.agent)
            if (l && seen.indexOf(l) < 0) seen.push(l)
        }
        return seen.join(", ")
    }

    Component.onCompleted: reload()
    Connections {
        target: Bridge
        function onHistoryChanged(json) { root.reload() }
    }

    C.ScrollPage {
        anchors.fill: parent
        spacing: 16

        // Cabecalho
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Text {
                text: "Histórico"
                color: C.Theme.textPrimary
                font.family: C.Theme.fontDisplay
                font.pixelSize: C.Theme.sizeXl + 4
                font.weight: Font.DemiBold
            }
            Item { Layout.fillWidth: true }
            Text {
                visible: root.stats.total > 0
                text: root.stats.total + " execuções  ·  " + root.stats.success_rate.toFixed(0)
                      + "% com sucesso  ·  " + root.fmtCost(root.stats.total_cost_usd) + " no total"
                color: C.Theme.textTertiary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeSm
            }
        }

        // Busca
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            radius: C.Theme.rMd
            color: C.Theme.bgSurface
            border.width: 1
            border.color: search.activeFocus ? C.Theme.hairlineHi : C.Theme.hairline
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8
                C.Icon { glyph: ""; size: 13; color: C.Theme.textTertiary }
                TextField {
                    id: search
                    Layout.fillWidth: true
                    placeholderText: "Buscar no histórico"
                    placeholderTextColor: C.Theme.textTertiary
                    color: C.Theme.textPrimary
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeMd
                    background: null
                    padding: 0
                    onTextChanged: root.query = text
                }
            }
        }

        // Vazio
        ColumnLayout {
            visible: root.filtered.length === 0
            Layout.fillWidth: true
            Layout.topMargin: 48
            spacing: 6
            C.Icon {
                Layout.alignment: Qt.AlignHCenter
                glyph: ""; size: 28; color: C.Theme.textTertiary
            }
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: root.items.length === 0 ? "Nenhuma execução ainda" : "Nada encontrado"
                color: C.Theme.textSecondary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
            }
        }

        // Lista
        ColumnLayout {
            visible: root.filtered.length > 0
            Layout.fillWidth: true
            spacing: 0

            Repeater {
                model: root.filtered
                delegate: Rectangle {
                    id: rowItem
                    Layout.fillWidth: true
                    implicitHeight: rowCol.implicitHeight + 24
                    radius: C.Theme.rMd
                    color: rowMouse.containsMouse ? C.Theme.bgHover : "transparent"

                    readonly property var it: modelData
                    readonly property bool clarify: it.error === "clarification_required"
                                                    || (it.error || "").indexOf("limitation") === 0

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 12

                        C.Icon {
                            Layout.alignment: Qt.AlignTop
                            Layout.topMargin: 14
                            size: 12
                            glyph: rowItem.it.success ? "" : rowItem.clarify ? "" : ""
                            color: rowItem.it.success ? C.Theme.success
                                 : rowItem.clarify ? C.Theme.info : C.Theme.danger
                        }

                        ColumnLayout {
                            id: rowCol
                            Layout.fillWidth: true
                            spacing: 3
                            Text {
                                Layout.fillWidth: true
                                text: rowItem.it.task || ""
                                color: C.Theme.textPrimary
                                font.family: C.Theme.fontSans
                                font.pixelSize: C.Theme.sizeMd
                                elide: Text.ElideRight
                                textFormat: Text.PlainText
                            }
                            Text {
                                Layout.fillWidth: true
                                text: {
                                    const p = [root.fmtWhen(rowItem.it.started_at),
                                               root.fmtDuration(rowItem.it.duration_ms)]
                                    const a = root.agentsOf(rowItem.it)
                                    if (a) p.push(a)
                                    const c = (rowItem.it.metrics || {}).cost_usd || 0
                                    if (c > 0) p.push(root.fmtCost(c))
                                    if (rowItem.it.dry_run) p.push("simulação")
                                    if (rowItem.clarify) p.push((rowItem.it.error || "").indexOf("limitation") === 0
                                                                ? "recusado pelo Maestro" : "pediu mais detalhes")
                                    return p.join("  ·  ")
                                }
                                color: C.Theme.textTertiary
                                font.family: C.Theme.fontSans
                                font.pixelSize: C.Theme.sizeSm
                                elide: Text.ElideRight
                            }
                        }

                        C.Button {
                            Layout.alignment: Qt.AlignVCenter
                            opacity: rowMouse.containsMouse ? 1 : 0
                            text: "Usar de novo"
                            icon: ""
                            compact: true
                            variant: "ghost"
                            onClicked: root.reuseRequested(rowItem.it.task || "")
                        }
                    }

                    MouseArea {
                        id: rowMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton
                    }

                    // Divisor
                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        height: 1
                        color: C.Theme.hairline
                        visible: index < root.filtered.length - 1 && !rowMouse.containsMouse
                    }
                }
            }
        }
    }
}
