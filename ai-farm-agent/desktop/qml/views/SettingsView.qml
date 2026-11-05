// Configuracoes: instrucoes personalizadas (valem para todo pedido), como o agente executa,
// voz e interface. Grava em desktop/data/settings.json (Bridge.saveSettings).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Item {
    id: root

    property var s: ({})
    property bool dirty: false
    property string savedMsg: ""

    function reload() {
        s = JSON.parse(Bridge.getSettings())
        instructions.text = s.instructions || ""
        dirty = false
    }
    function save(patch) {
        const out = JSON.parse(Bridge.saveSettings(JSON.stringify(patch)))
        if (out.ok) {
            s = Object.assign({}, s, out)
            savedMsg = "Salvo"
            savedTimer.restart()
        }
    }
    Timer { id: savedTimer; interval: 1800; onTriggered: root.savedMsg = "" }
    Component.onCompleted: reload()
    onVisibleChanged: if (visible) reload()

    C.ScrollPage {
        anchors.fill: parent
        maxWidth: 680
        spacing: 26

        Text {
            text: "Configurações"
            color: C.Theme.textPrimary
            font.family: C.Theme.fontDisplay
            font.pixelSize: C.Theme.sizeHero - 6
            font.weight: Font.DemiBold
        }

        // ── Instrucoes personalizadas ───────────────────────────────
        Section {
            title: "Instruções personalizadas"
            note: "Valem para todo pedido, como as instruções de projeto do Claude e do ChatGPT. "
                + "São preferências: não liberam nada que o agente não possa fazer."
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 130
                radius: C.Theme.rMd
                color: C.Theme.bgSurface
                border.width: 1
                border.color: instructions.activeFocus ? C.Theme.alpha(C.Theme.accent, 0.45) : C.Theme.hairline
                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 10
                    TextArea {
                        id: instructions
                        wrapMode: TextArea.Wrap
                        placeholderText: "Ex.: responda curto e direto · planilhas sempre em R$ com gráfico · "
                                       + "salve arquivos na pasta Documentos/IA"
                        placeholderTextColor: C.Theme.textTertiary
                        color: C.Theme.textPrimary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeMd
                        background: null
                        onTextChanged: root.dirty = text !== (root.s.instructions || "")
                        Keys.onPressed: (e) => {
                            if (text.length >= 1500 && e.text && e.key !== Qt.Key_Backspace) e.accepted = true
                        }
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    text: instructions.text.length + " / 1500"
                    color: C.Theme.textTertiary
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeXs
                }
                Text {
                    visible: root.savedMsg !== ""
                    text: root.savedMsg
                    color: C.Theme.success
                    font.family: C.Theme.fontSans
                    font.pixelSize: C.Theme.sizeSm
                }
                C.Button {
                    text: "Salvar"
                    variant: "primary"
                    compact: true
                    enabled: root.dirty
                    onClicked: { root.save({ instructions: instructions.text }); root.dirty = false }
                }
            }
        }

        // ── Execucao ────────────────────────────────────────────────
        Section {
            title: "Execução"
            SettingSwitch {
                label: "Revisar o plano antes de executar"
                detail: "Mostra os passos e espera você aprovar antes de mexer no PC (pedidos digitados). "
                      + "Como no Cowork e no ChatGPT Work."
                checked: !!root.s.plan_review
                onToggled: (v) => root.save({ plan_review: v })
            }
        }

        // ── Voz ─────────────────────────────────────────────────────
        Section {
            title: "Voz"
            note: "Voz sintetizada por IA. Fora do modo Conversa, o microfone e a transcrição ficam no computador."
            SettingSwitch {
                label: "Conversa em tempo real com GPT-Live"
                detail: "No modo Conversa, o áudio do microfone vai para a OpenAI enquanto há conversa. Cobrado por "
                      + "segundo de sessão aberta (cerca de US$ 3 por hora); fecha sozinha sem atividade. "
                      + "Desligado, a conversa usa a transcrição local."
                checked: root.s.live_conversation !== false
                onToggled: (v) => root.save({ live_conversation: v })
            }
            SettingSwitch {
                label: "Interromper falando"
                detail: "Fale por cima do agente e ele se cala na hora para ouvir você."
                checked: root.s.barge_in !== false
                onToggled: (v) => root.save({ barge_in: v })
            }
            SettingSwitch {
                label: "Sinal sonoro ao terminar de falar"
                detail: "Um toque curto confirma que a fala chegou, antes da resposta."
                checked: root.s.earcon !== false
                onToggled: (v) => root.save({ earcon: v })
            }
        }

        // ── Interface ───────────────────────────────────────────────
        Section {
            title: "Interface"
            note: "Vale a partir da próxima vez que o app abrir."
            SettingSwitch {
                label: "Tela de abertura"
                checked: root.s.splash !== false
                onToggled: (v) => root.save({ splash: v })
            }
            SettingSwitch {
                label: "Mini chat quando o agente vai para outro app"
                checked: root.s.mini_chat !== false
                onToggled: (v) => root.save({ mini_chat: v })
            }
        }

        // ── Atalhos ─────────────────────────────────────────────────
        Section {
            title: "Atalhos"
            Repeater {
                model: [
                    { k: "Acesso rápido (de qualquer app)", v: (root.s.hotkeys || {}).quick },
                    { k: "Gravar / conversar por voz", v: (root.s.hotkeys || {}).voice },
                    { k: "Parar a execução", v: (root.s.hotkeys || {}).stop },
                ]
                delegate: RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: modelData.k
                        color: C.Theme.textPrimary
                        font.family: C.Theme.fontSans
                        font.pixelSize: C.Theme.sizeMd
                    }
                    Rectangle {
                        implicitWidth: keyText.implicitWidth + 16
                        implicitHeight: 24
                        radius: 6
                        color: C.Theme.bgSurfaceHi
                        Text {
                            id: keyText
                            anchors.centerIn: parent
                            text: modelData.v ? modelData.v.split("+").map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(" + ")
                                              : "indisponível"
                            color: C.Theme.textSecondary
                            font.family: C.Theme.fontMono
                            font.pixelSize: C.Theme.sizeSm
                        }
                    }
                }
            }
            Text {
                Layout.fillWidth: true
                text: "Os atalhos ficam em config.yaml (seções ui e voice)."
                color: C.Theme.textTertiary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeSm
                wrapMode: Text.Wrap
            }
        }
    }

    // ── Pecas locais ────────────────────────────────────────────────
    component Section: ColumnLayout {
        property string title: ""
        property string note: ""
        default property alias content: inner.data
        Layout.fillWidth: true
        spacing: 10
        Text {
            text: parent.title
            color: C.Theme.textPrimary
            font.family: C.Theme.fontSans
            font.pixelSize: C.Theme.sizeLg
            font.weight: Font.DemiBold
        }
        Text {
            visible: parent.note !== ""
            Layout.fillWidth: true
            text: parent.note
            color: C.Theme.textSecondary
            font.family: C.Theme.fontSans
            font.pixelSize: C.Theme.sizeSm + 1
            wrapMode: Text.Wrap
        }
        ColumnLayout {
            id: inner
            Layout.fillWidth: true
            spacing: 12
        }
    }

    component SettingSwitch: RowLayout {
        id: sw
        property string label: ""
        property string detail: ""
        property bool checked: false
        signal toggled(bool value)
        Layout.fillWidth: true
        spacing: 14
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                Layout.fillWidth: true
                text: sw.label
                color: C.Theme.textPrimary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeMd
                wrapMode: Text.Wrap
            }
            Text {
                visible: sw.detail !== ""
                Layout.fillWidth: true
                text: sw.detail
                color: C.Theme.textTertiary
                font.family: C.Theme.fontSans
                font.pixelSize: C.Theme.sizeSm
                wrapMode: Text.Wrap
            }
        }
        Rectangle {
            implicitWidth: 40
            implicitHeight: 22
            radius: 11
            color: sw.checked ? C.Theme.accent : C.Theme.bgSurfaceHi
            border.width: sw.checked ? 0 : 1
            border.color: C.Theme.hairlineHi
            Behavior on color { ColorAnimation { duration: C.Theme.durFast } }
            Rectangle {
                width: 16; height: 16; radius: 8
                y: 3
                x: sw.checked ? parent.width - width - 3 : 3
                color: "white"
                Behavior on x { NumberAnimation { duration: C.Theme.durFast; easing.type: Easing.OutCubic } }
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: sw.toggled(!sw.checked)
            }
            Accessible.role: Accessible.CheckBox
            Accessible.name: sw.label
            Accessible.checked: sw.checked
        }
    }
}
