// Sobre: o que o app faz, como funciona e quem faz o que. So o essencial.
import QtQuick
import QtQuick.Layouts
import "../components" as C

Item {
    id: root

    C.ScrollPage {
        anchors.fill: parent
        maxWidth: 680
        spacing: 28

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10
            Text {
                text: "AI Farm Agent"
                color: C.Theme.textPrimary
                font.family: C.Theme.fontDisplay
                font.pixelSize: C.Theme.sizeHero
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                text: "Você descreve o que precisa em linguagem natural e um time de agentes "
                    + "de IA executa no seu computador: cria planilhas e projetos, navega na web, "
                    + "organiza arquivos e opera aplicativos do Windows."
                color: C.Theme.textSecondary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeLg - 1
                lineHeight: 1.35
                wrapMode: Text.Wrap
            }
        }

        Section {
            title: "Como funciona"
            Repeater {
                model: [
                    { n: "1", t: "Entender", d: "O Maestro lê o pedido, pergunta se faltar algo e divide em etapas." },
                    { n: "2", t: "Planejar", d: "Cada etapa vai para o agente especialista, que monta os passos." },
                    { n: "3", t: "Executar", d: "Os passos rodam no seu computador e você acompanha em tempo real." },
                ]
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    Rectangle {
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                        Layout.alignment: Qt.AlignTop
                        radius: 12
                        color: C.Theme.bgSurfaceHi
                        Text {
                            anchors.centerIn: parent
                            text: modelData.n
                            color: C.Theme.textPrimary
                            font.family: C.Theme.fontSans
                            font.pixelSize: C.Theme.sizeSm
                            font.weight: Font.DemiBold
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: modelData.t
                            color: C.Theme.textPrimary
                            font.family: C.Theme.fontSans
                            font.pixelSize: C.Theme.sizeMd
                            font.weight: Font.Medium
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.d
                            color: C.Theme.textSecondary
                            font.family: C.Theme.fontSans
                            font.pixelSize: C.Theme.sizeMd
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }

        Section {
            title: "Agentes"
            Repeater {
                model: [
                    { i: "", n: "Maestro",  d: "Entende o pedido e distribui o trabalho" },
                    { i: "", n: "Código",   d: "Cria sites, scripts e sistemas completos" },
                    { i: "", n: "Dados",    d: "Monta planilhas Excel com fórmulas e gráficos" },
                    { i: "", n: "Web",      d: "Pesquisa e navega em sites" },
                    { i: "", n: "Desktop",  d: "Opera apps como Teams, Word e Bloco de Notas" },
                    { i: "", n: "Arquivos", d: "Organiza, move e encontra arquivos" },
                    { i: "", n: "Memória",  d: "Lembra quais caminhos funcionaram, sem repetir conteúdo" },
                ]
                delegate: RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    spacing: 14
                    C.Icon { glyph: modelData.i; size: 15; Layout.preferredWidth: 20 }
                    Text {
                        text: modelData.n
                        color: C.Theme.textPrimary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeMd
                        font.weight: Font.Medium
                        Layout.preferredWidth: 90
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.d
                        color: C.Theme.textSecondary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeMd
                        elide: Text.ElideRight
                    }
                }
            }
            Text {
                Layout.topMargin: 6
                Layout.fillWidth: true
                text: "Todos os agentes usam Claude Sonnet 5."
                color: C.Theme.textTertiary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeSm
            }
        }

        Section {
            title: "Desenvolvido por"
            Text {
                text: "Guilherme Moraes Franco"
                color: C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
                font.weight: Font.Medium
            }
            Flow {
                Layout.fillWidth: true
                spacing: 8
                Repeater {
                    model: [
                        { l: "GitHub",    u: "https://github.com/ognistie" },
                        { l: "Portfólio", u: "https://ognistie.github.io/portfolio/" },
                        { l: "LinkedIn",  u: "https://www.linkedin.com/in/guilherme-moraes-franco-b4b1a0353/" },
                    ]
                    delegate: C.Button {
                        text: modelData.l
                        icon: ""
                        compact: true
                        onClicked: Qt.openUrlExternally(modelData.u)
                    }
                }
            }
        }
    }

    component Section: ColumnLayout {
        property string title: ""
        Layout.fillWidth: true
        spacing: 10
        Text {
            text: parent.title
            color: C.Theme.textTertiary
            font.family: C.Theme.fontSans
            font.pixelSize: C.Theme.sizeSm
            font.weight: Font.Medium
            Layout.bottomMargin: 2
        }
    }
}
