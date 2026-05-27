// Activity — registro do que o agente fez: arquivos abertos, pastas criadas,
// comandos executados, sites visitados. Categorizado e filtravel.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Item {
    id: root

    // Cada item: { ts, agent, category, icon, title, detail, action, ok }
    ListModel { id: allActivity }
    ListModel { id: shownActivity }

    property string filter: "all"   // all | files | code | web | desktop | data
    property string search: ""
    property int countFiles: 0
    property int countCode: 0
    property int countWeb: 0
    property int countDesktop: 0
    property int countData: 0

    // ── Mapeamento de actions para categorias ──────────────────────
    function categorize(action) {
        const a = (action || "").toLowerCase()
        if (a === "write_file" || a === "create_folder" || a === "read_file"
            || a === "list_files" || a === "move_file" || a === "copy_file"
            || a === "delete_file" || a === "find_files")
            return { cat: "files", icon: "📂", label: "Arquivo" }
        if (a === "run_python" || a === "run_command" || a === "pip_install")
            return { cat: "code", icon: "▣", label: "Codigo" }
        if (a.indexOf("playwright") >= 0 || a === "open_url" || a === "navigate"
            || a === "browser_click" || a === "browser_type" || a === "browser_screenshot")
            return { cat: "web", icon: "🌐", label: "Web" }
        if (a === "app_search" || a === "app_type" || a === "focus_window"
            || a === "hotkey" || a === "type_text" || a.startsWith("uia_")
            || a.startsWith("vision_") || a === "wait_for_window" || a === "wait_for_element")
            return { cat: "desktop", icon: "🖥", label: "Desktop" }
        if (a === "excel_write" || a === "excel_read")
            return { cat: "data", icon: "📊", label: "Dados" }
        return { cat: "other", icon: "·", label: "Outro" }
    }

    // Extrai o "objeto" da acao a partir do desc + result (caminho/url/comando)
    function extractTarget(action, desc, result) {
        const r = (result || "").toString().substring(0, 120)
        // Pasta / arquivo no result
        const pathMatch = r.match(/([A-Z]:\\[\w\-\\\./ ]+|\/[\w\-\/\.]+)/i)
        if (pathMatch) return pathMatch[1]
        // URL
        const urlMatch = r.match(/(https?:\/\/[^\s]+)/)
        if (urlMatch) return urlMatch[1]
        return desc || ""
    }

    function pushActivity(entry) {
        allActivity.append(entry)
        switch (entry.category) {
            case "files":   countFiles++; break
            case "code":    countCode++; break
            case "web":     countWeb++; break
            case "desktop": countDesktop++; break
            case "data":    countData++; break
        }
        refilter()
    }

    function refilter() {
        shownActivity.clear()
        const q = root.search.toLowerCase()
        for (let i = 0; i < allActivity.count; i++) {
            const e = allActivity.get(i)
            if (root.filter !== "all" && e.category !== root.filter) continue
            if (q && e.title.toLowerCase().indexOf(q) < 0
                  && (e.detail || "").toLowerCase().indexOf(q) < 0) continue
            shownActivity.append(e)
        }
    }

    // ── Helper para timestamps consistentes ─────────────────────────
    function now() {
        return new Date().toLocaleTimeString(Qt.locale("pt_BR"))
    }

    // ── Listeners do bus (captura TODO o ciclo de vida da tarefa) ──
    // Antes capturava so step_done + context. Resultado: se a tarefa
    // falhasse no validator (antes de executar steps), a Activity ficava
    // VAZIA. Agora capturamos: phase, plan, step, log, error, taskDone.
    Connections {
        target: Bridge

        function onPhaseChanged(json) {
            const p = JSON.parse(json)
            const msg = p.msg || p.phase || ""
            if (!msg) return
            root.pushActivity({
                ts: root.now(),
                agent: "MAESTRO",
                category: "other",
                catLabel: "Fase",
                icon: "▸",
                title: msg,
                detail: "fase: " + (p.phase || ""),
                action: "phase_" + (p.phase || ""),
                ok: true,
            })
        }

        function onPlanReady(json) {
            const data = JSON.parse(json).plan
            const steps = (data && data.steps) || []
            root.pushActivity({
                ts: root.now(),
                agent: "MAESTRO",
                category: "other",
                catLabel: "Plano",
                icon: "◆",
                title: "Plano gerado (" + steps.length + " subtarefa(s))",
                detail: steps.map(function(s){return s.description || s.action}).join(" | "),
                action: "plan_ready",
                ok: true,
            })
        }

        function onStepStart(json) {
            const s = JSON.parse(json)
            const tag = (s.desc || "").match(/\[(\w+)\]/)
            const agent = tag ? tag[1].toUpperCase() : "SYSTEM"
            root.pushActivity({
                ts: root.now(),
                agent: agent,
                category: "other",
                catLabel: "Inicio",
                icon: "▶",
                title: "Iniciando: " + (s.desc || "").replace(/\[\w+\]\s*/, ""),
                detail: "step " + (s.step || "?") + "/" + (s.total || "?"),
                action: s.action || "",
                ok: true,
            })
        }

        function onStepDone(json) {
            const s = JSON.parse(json)
            const tag = (s.desc || "").match(/\[(\w+)\]/)
            const agent = tag ? tag[1].toUpperCase() : "SYSTEM"
            const cat = root.categorize(s.action)
            const target = root.extractTarget(s.action, s.desc, s.result)
            root.pushActivity({
                ts: root.now(),
                agent: agent,
                category: cat.cat,
                catLabel: cat.label,
                icon: cat.icon,
                title: (s.desc || "").replace(/\[\w+\]\s*/, ""),
                detail: target,
                action: s.action || "",
                ok: !!s.ok,
            })
        }

        function onLogEntry(json) {
            const e = JSON.parse(json)
            const level = (e.level || "INFO").toUpperCase()
            // Filtramos DEBUG (ruido). Mostramos INFO/WARN/ERROR.
            if (level === "DEBUG") return
            const icon = level === "ERROR" ? "✕"
                       : level === "WARN"  ? "⚠"
                       : "·"
            root.pushActivity({
                ts: (e.ts || "").substring(11, 23) || root.now(),
                agent: (e.agent || "SYSTEM").toUpperCase(),
                category: "other",
                catLabel: level,
                icon: icon,
                title: e.msg || "",
                detail: e.extra ? JSON.stringify(e.extra).substring(0, 80) : "",
                action: "log_" + level.toLowerCase(),
                ok: level !== "ERROR" && level !== "WARN",
            })
        }

        function onContextExtracted(json) {
            const e = JSON.parse(json)
            if (e.folder) {
                root.pushActivity({
                    ts: root.now(),
                    agent: e.agent || "SYSTEM",
                    category: "files",
                    catLabel: "Arquivo",
                    icon: "📂",
                    title: "Pasta criada",
                    detail: e.folder,
                    action: "create_folder",
                    ok: true,
                })
            }
            if (e.files && e.files.length) {
                root.pushActivity({
                    ts: root.now(),
                    agent: e.agent || "SYSTEM",
                    category: "files",
                    catLabel: "Arquivo",
                    icon: "📄",
                    title: e.files.length + " arquivo(s) gravado(s)",
                    detail: e.files.join(", "),
                    action: "write_files",
                    ok: true,
                })
            }
            if (e.url) {
                root.pushActivity({
                    ts: root.now(),
                    agent: e.agent || "SYSTEM",
                    category: "web",
                    catLabel: "Web",
                    icon: "🌐",
                    title: "URL acessada",
                    detail: e.url,
                    action: "open_url",
                    ok: true,
                })
            }
        }

        function onErrorRaised(json) {
            const e = JSON.parse(json)
            root.pushActivity({
                ts: root.now(),
                agent: "SYSTEM",
                category: "other",
                catLabel: "Erro",
                icon: "✕",
                title: "Erro: " + (e.msg || "").substring(0, 100),
                detail: e.kind || "",
                action: "error",
                ok: false,
            })
        }

        function onTaskDone(json) {
            const d = JSON.parse(json)
            root.pushActivity({
                ts: root.now(),
                agent: "SYSTEM",
                category: "other",
                catLabel: "Fim",
                icon: "✓",
                title: "Tarefa concluida (" + (d.steps || 0) + " step(s))",
                detail: (d.skills || []).join(", "),
                action: "task_done",
                ok: true,
            })
        }

        function onCancelled(json) {
            root.pushActivity({
                ts: root.now(),
                agent: "SYSTEM",
                category: "other",
                catLabel: "Cancelado",
                icon: "⊘",
                title: "Execucao cancelada",
                detail: "",
                action: "cancel",
                ok: false,
            })
        }
    }

    // ── Layout ───────────────────────────────────────────────────────
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 18

        // Header Mac-app style
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            Text {
                text: "ATIVIDADE"
                color: C.Theme.accent
                font.family: C.Theme.fontMono
                font.pixelSize: 10
                font.letterSpacing: 1.8
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                Text {
                    text: "O que o agente fez"
                    color: C.Theme.textPrimary
                    font.family: C.Theme.fontSans
                    font.pixelSize: 26
                    font.weight: Font.DemiBold
                    font.letterSpacing: -0.3
                }
                Item { Layout.fillWidth: true }
                Text {
                    text: shownActivity.count + " evento(s)"
                    color: C.Theme.textMuted
                    font.family: C.Theme.fontMono
                    font.pixelSize: 12
                    Layout.alignment: Qt.AlignVCenter
                }
            }
            Text {
                Layout.fillWidth: true
                text: "Todos os arquivos criados, comandos executados, sites visitados e janelas abertas durante a sessao."
                color: C.Theme.textSecondary
                font.family: C.Theme.fontSans
                font.pixelSize: 13
                wrapMode: Text.Wrap
            }
        }

        // Cards de resumo por categoria
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Repeater {
                model: [
                    { v: root.countFiles,   l: "Arquivos",  g: "📂", k: "files",   c: C.Theme.cyan },
                    { v: root.countCode,    l: "Codigo",    g: "▣",  k: "code",    c: C.Theme.accent },
                    { v: root.countWeb,     l: "Web",       g: "🌐", k: "web",     c: C.Theme.violet },
                    { v: root.countDesktop, l: "Desktop",   g: "🖥", k: "desktop", c: C.Theme.amber },
                    { v: root.countData,    l: "Dados",     g: "📊", k: "data",    c: C.Theme.info },
                ]
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 88
                    radius: C.Theme.rLg
                    color: root.filter === modelData.k
                        ? C.Theme.alpha(modelData.c, 0.10)
                        : C.Theme.bgSurface
                    border.color: root.filter === modelData.k
                        ? C.Theme.alpha(modelData.c, 0.45)
                        : C.Theme.hairline
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 4
                        RowLayout {
                            spacing: 6
                            Text { text: modelData.g; font.pixelSize: 16 }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: modelData.l.toUpperCase()
                                color: C.Theme.textMuted
                                font.family: C.Theme.fontMono
                                font.pixelSize: 9
                                font.letterSpacing: 1.4
                            }
                        }
                        Text {
                            text: modelData.v
                            color: C.Theme.textPrimary
                            font.family: C.Theme.fontSans
                            font.pixelSize: 24
                            font.weight: Font.Bold
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.filter = (root.filter === modelData.k) ? "all" : modelData.k
                            root.refilter()
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 140 } }
                }
            }
        }

        // Filtros + busca
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 320
                Layout.preferredHeight: 34
                color: C.Theme.bgInput
                radius: C.Theme.rMd
                border.color: searchInput.activeFocus ? C.Theme.accent : C.Theme.hairlineHi
                border.width: 1
                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    spacing: 8
                    Text {
                        text: "🔍"; color: C.Theme.textMuted
                        font.pixelSize: 11
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    TextField {
                        id: searchInput
                        width: parent.width - 24
                        anchors.verticalCenter: parent.verticalCenter
                        placeholderText: "Buscar na atividade..."
                        color: C.Theme.textPrimary
                        placeholderTextColor: C.Theme.textMuted
                        font.family: C.Theme.fontSans
                        font.pixelSize: 12
                        background: null
                        onTextChanged: { root.search = text; root.refilter() }
                    }
                }
            }

            // Chip "Tudo"
            C.Chip {
                text: "Tudo (" + allActivity.count + ")"
                selected: root.filter === "all"
                onClicked: { root.filter = "all"; root.refilter() }
            }

            Item { Layout.fillWidth: true }

            C.GhostButton {
                text: "Limpar"
                onClicked: {
                    allActivity.clear()
                    shownActivity.clear()
                    root.countFiles = 0
                    root.countCode = 0
                    root.countWeb = 0
                    root.countDesktop = 0
                    root.countData = 0
                }
            }
        }

        // Lista
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: C.Theme.rLg
            color: C.Theme.bgSurface
            border.color: C.Theme.hairline
            border.width: 1

            // Estado vazio
            ColumnLayout {
                anchors.centerIn: parent
                visible: shownActivity.count === 0
                spacing: 8
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "≡"
                    color: C.Theme.textMuted
                    font.pixelSize: 36
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Sem atividade ainda"
                    color: C.Theme.textSecondary
                    font.family: C.Theme.fontSans
                    font.pixelSize: 14
                    font.weight: Font.Medium
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Execute uma tarefa no Command Center — cada acao aparece aqui."
                    color: C.Theme.textMuted
                    font.family: C.Theme.fontSans
                    font.pixelSize: 12
                }
            }

            ListView {
                id: activityList
                anchors.fill: parent
                anchors.margins: 10
                model: shownActivity
                visible: shownActivity.count > 0
                clip: true
                spacing: 4
                onCountChanged: positionViewAtEnd()

                delegate: Rectangle {
                    width: activityList.width
                    height: 56
                    color: index % 2 === 0 ? "transparent" : Qt.rgba(1,1,1,0.012)
                    radius: 6

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 12

                        // Icone categoria + faixa colorida
                        Rectangle {
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            radius: 8
                            color: C.Theme.bgSurfaceHi
                            border.color: C.Theme.hairline
                            border.width: 1
                            Text {
                                anchors.centerIn: parent
                                text: model.icon
                                font.pixelSize: 16
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text {
                                    text: model.title
                                    color: C.Theme.textPrimary
                                    font.family: C.Theme.fontSans
                                    font.pixelSize: 13
                                    font.weight: Font.Medium
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                C.AgentBadge { agent: model.agent }
                                Rectangle {
                                    width: 6; height: 6; radius: 3
                                    color: model.ok ? C.Theme.accent : C.Theme.coral
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: !!model.detail
                                text: model.detail || ""
                                color: C.Theme.textMuted
                                font.family: C.Theme.fontMono
                                font.pixelSize: 11
                                elide: Text.ElideMiddle
                            }
                        }

                        Text {
                            text: model.action
                            color: C.Theme.textMuted
                            font.family: C.Theme.fontMono
                            font.pixelSize: 10
                            Layout.preferredWidth: 110
                            horizontalAlignment: Text.AlignRight
                            elide: Text.ElideRight
                        }
                        Text {
                            text: model.ts
                            color: C.Theme.textMuted
                            font.family: C.Theme.fontMono
                            font.pixelSize: 10
                            Layout.preferredWidth: 70
                            horizontalAlignment: Text.AlignRight
                        }
                    }
                }
            }
        }
    }
}
