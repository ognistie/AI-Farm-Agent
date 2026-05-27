// About — preserva integralmente o conteudo do HTML antigo:
// objetivo, equipe de 8 agentes, cascata L1→L3, self-healing + stack,
// perfil do desenvolvedor. Layout 100% baseado em RowLayout/ColumnLayout
// para evitar polish loops do QtQuick (bug recorrente em Row + width=parent.width-N).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Item {
    id: root

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true
        // Barras invisiveis — rolagem ainda funciona via wheel / trackpad
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: root.width
            spacing: 18

            // ── Cabecalho ──────────────────────────────────────────
            ColumnLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.topMargin: 24
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    C.HexLogo { sizePx: 28; tone: C.Theme.accent }
                    Text {
                        text: "O Sistema"
                        color: C.Theme.textPrimary
                        font.family: C.Theme.fontSans
                        font.pixelSize: 26
                        font.weight: Font.Bold
                    }
                    C.Pill { text: "v2.0 DESKTOP"; tone: C.Theme.cyan }
                    Item { Layout.fillWidth: true }
                }
                Text {
                    Layout.fillWidth: true
                    text: "Ensinando computadores a operarem sozinhos."
                    color: C.Theme.textSecondary
                    font.family: C.Theme.fontSans
                    font.pixelSize: 14
                }
            }

            // ── Objetivo primario ─────────────────────────────────
            C.Card {
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.preferredHeight: 200
                title: "Objetivo Primario"
                subtitle: "Da linguagem natural ao mundo real"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    anchors.topMargin: 10
                    spacing: 10
                    Text {
                        Layout.fillWidth: true
                        text: "O <b>AI Farm Agent</b> nao enxerga seu computador apenas como pixels, mas como um mundo estruturado de janelas, botoes e workflows que podem ser controlados. E um sistema multi-agente autonomo que transforma <i>linguagem natural</i> em <i>acoes reais</i>."
                        color: C.Theme.textPrimary
                        textFormat: Text.RichText
                        font.family: C.Theme.fontSans
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                        lineHeight: 1.55
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Ele pensa, planeja, executa e verifica — criando planilhas no Excel, enviando mensagens, organizando arquivos e navegando na web de forma 100% autonoma."
                        color: C.Theme.textSecondary
                        font.family: C.Theme.fontSans
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                        lineHeight: 1.55
                    }
                }
            }

            // ── Eyebrow Equipe ─────────────────────────────────────
            Text {
                Layout.leftMargin: 24
                Layout.topMargin: 8
                text: "A EQUIPE DE AGENTES"
                color: C.Theme.accent
                font.family: C.Theme.fontMono
                font.pixelSize: 10
                font.letterSpacing: 2
            }

            // ── Grid Equipe ────────────────────────────────────────
            GridLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                columns: Math.max(1, Math.min(4, Math.floor((root.width - 60) / 290)))
                columnSpacing: 12
                rowSpacing: 12

                Repeater {
                    model: [
                        { icon:"🧠", n:"MAESTRO",       m:"Haiku 4.5", accent:false, d:"O cerebro. Roteia cada tarefa para o especialista certo, decompoe pedidos complexos e coordena a ordem de execucao." },
                        { icon:"📊", n:"DATA AGENT",    m:"Haiku 4.5", accent:false, d:"O analista. Cria planilhas, graficos e analises de dados gerando codigo Python puro via openpyxl." },
                        { icon:"💻", n:"CODE AGENT",    m:"Sonnet 4",  accent:true,  d:"O construtor. Cria projetos completos (HTML, CSS, JS, Python) com qualidade de producao." },
                        { icon:"🌐", n:"WEB AGENT",     m:"Haiku 4.5", accent:false, d:"O navegador. Domina a web usando Playwright. Lida com cookies, popups e formularios complexos." },
                        { icon:"🖥", n:"DESKTOP AGENT",  m:"Sonnet 4",  accent:true,  d:"O operador. Interage com qualquer app Windows via UIA + Vision. Atalhos para Teams, Word, Outlook." },
                        { icon:"👁", n:"VISION MAESTRO", m:"Haiku 4.5", accent:false, d:"O vigia. Captura e analisa a tela antes e depois das acoes. Detecta erros, popups e estados de carregamento." },
                        { icon:"📁", n:"FILE AGENT",    m:"Haiku 4.5", accent:false, d:"O organizador. Gerencia pastas e arquivos via os/shutil. Organiza downloads e estruturas de diretorios." },
                        { icon:"🗄", n:"MEMORY AGENT",  m:"Core",      accent:false, d:"O arquivista. Armazena em cache fluxos bem-sucedidos para pular planejamento no futuro." },
                    ]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 160
                        color: C.Theme.bgSurface
                        radius: C.Theme.rLg
                        border.color: C.Theme.hairline
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 16
                            spacing: 6

                            Text { text: modelData.icon; font.pixelSize: 22 }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text {
                                    text: modelData.n
                                    color: C.Theme.textPrimary
                                    font.family: C.Theme.fontSans
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                }
                                Item { Layout.fillWidth: true }
                                C.Pill {
                                    text: modelData.m
                                    tone: modelData.accent ? C.Theme.amber : C.Theme.textSecondary
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: modelData.d
                                color: C.Theme.textSecondary
                                font.family: C.Theme.fontSans
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                                lineHeight: 1.45
                            }
                        }
                    }
                }
            }

            // ── Arquitetura: Cascata + Self-healing ───────────────
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.topMargin: 8
                spacing: 12

                // Cascata L1/L2/L3
                C.Card {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 240
                    title: "Cascata de Interacao"
                    subtitle: "L1 → L2 → L3 · fallback automatico"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        anchors.topMargin: 10
                        spacing: 10

                        Text {
                            Layout.fillWidth: true
                            text: "A inovacao central. O sistema desce por 3 niveis de confiabilidade, caindo para o proximo apenas se o atual falhar."
                            color: C.Theme.textSecondary
                            font.family: C.Theme.fontSans
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                        }

                        Repeater {
                            model: [
                                { lvl: "L1", d: "API / Codigo direto (openpyxl, Playwright)", v: 99, tone: C.Theme.accent },
                                { lvl: "L2", d: "UI Automation (pywinauto)", v: 95, tone: C.Theme.cyan },
                                { lvl: "L3", d: "Vision + PyAutoGUI (fallback)", v: 80, tone: C.Theme.coral },
                            ]
                            delegate: ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Text {
                                        text: modelData.lvl
                                        color: modelData.tone
                                        font.family: C.Theme.fontMono
                                        font.pixelSize: 11
                                        font.weight: Font.Bold
                                        Layout.preferredWidth: 22
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.d
                                        color: C.Theme.textPrimary
                                        font.family: C.Theme.fontSans
                                        font.pixelSize: 12
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        text: modelData.v + "%"
                                        color: modelData.tone
                                        font.family: C.Theme.fontMono
                                        font.pixelSize: 11
                                    }
                                }
                                C.ProgressBar {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 4
                                    value: modelData.v
                                    tone: modelData.tone
                                }
                            }
                        }
                    }
                }

                // Self-healing + stack
                C.Card {
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 240
                    title: "Self-Healing & Stack"
                    subtitle: "5 estrategias de recuperacao · tech stack"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        anchors.topMargin: 10
                        spacing: 10

                        Text {
                            Layout.fillWidth: true
                            text: "O <b>Retry Engine</b> diagnostica falhas e aplica 5 estrategias de recuperacao (Wait, Alternative Path, Recover State, Escalate, Abort) garantindo estabilidade autonoma."
                            color: C.Theme.textPrimary
                            textFormat: Text.RichText
                            font.family: C.Theme.fontSans
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                            lineHeight: 1.45
                        }
                        Text {
                            text: "TECNOLOGIAS BASE"
                            color: C.Theme.cyan
                            font.family: C.Theme.fontMono
                            font.pixelSize: 10
                            font.letterSpacing: 1.6
                            topPadding: 6
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            Repeater {
                                model: ["Python 3.11+","Claude API","PySide6 / QML","pywinauto","Playwright","EasyOCR"]
                                delegate: C.Pill { text: modelData; tone: C.Theme.textSecondary }
                            }
                        }
                    }
                }
            }

            // ── Perfil do Desenvolvedor ────────────────────────────
            C.Card {
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                Layout.bottomMargin: 24
                Layout.topMargin: 8
                Layout.preferredHeight: 200
                title: "Perfil do Desenvolvedor"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    anchors.topMargin: 14
                    spacing: 24

                    Rectangle {
                        Layout.preferredWidth: 88
                        Layout.preferredHeight: 88
                        radius: 44
                        color: C.Theme.bgInput
                        border.color: C.Theme.accent
                        border.width: 2
                        Layout.alignment: Qt.AlignVCenter

                        Text {
                            anchors.centerIn: parent
                            text: "GF"
                            color: C.Theme.accent
                            font.family: C.Theme.fontSans
                            font.pixelSize: 28
                            font.weight: Font.Bold
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                        spacing: 6

                        Text {
                            text: "Guilherme Moraes Franco"
                            color: C.Theme.textPrimary
                            font.family: C.Theme.fontSans
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Full Stack & Cloud Engineering · Estagiario de TI na IT Universe"
                            color: C.Theme.textSecondary
                            font.family: C.Theme.fontSans
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                        Flow {
                            Layout.fillWidth: true
                            Layout.topMargin: 6
                            spacing: 6
                            Repeater {
                                model: ["AWS","Azure","Python","Linux","DevOps","Docker"]
                                delegate: C.Pill { text: modelData; tone: C.Theme.textSecondary }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.topMargin: 10
                            spacing: 16
                            Repeater {
                                model: [
                                    {l:"GitHub",    u:"https://github.com/ognistie"},
                                    {l:"Portfolio", u:"https://ognistie.github.io/portfolio/"},
                                    {l:"LinkedIn",  u:"https://www.linkedin.com/in/guilherme-moraes-franco-b4b1a0353/"},
                                    {l:"Email",     u:"mailto:og.guifranco@gmail.com"},
                                ]
                                delegate: Text {
                                    text: modelData.l + " ↗"
                                    color: C.Theme.accent
                                    font.family: C.Theme.fontMono
                                    font.pixelSize: 11
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: Qt.openUrlExternally(modelData.u)
                                    }
                                }
                            }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }
            }
        }
    }
}
