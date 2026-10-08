// Circulo de status (passo, pedido, resultado): verde com check, ambar com
// exclamacao (pergunta/aviso), cinza (interrompido) ou vermelho com x.
import QtQuick

Rectangle {
    id: root
    property string status: "ok"   // ok|done | warn|clarify|limited | cancelled | fail|failed
    property int size: 15
    readonly property bool good: status === "ok" || status === "done"
    readonly property bool caution: status === "warn" || status === "clarify" || status === "limited"

    width: size; height: size; radius: size / 2
    color: good ? Theme.success : caution ? Theme.warning
         : status === "cancelled" ? Theme.textTertiary : Theme.danger

    Icon {
        anchors.centerIn: parent
        size: Math.round(root.size * 0.55)
        color: Theme.textInverse
        glyph: root.good ? "" : root.status === "cancelled" ? ""
             : root.caution ? "" : ""
    }

    Accessible.role: Accessible.Indicator
    Accessible.name: root.good ? "Concluído" : root.caution ? "Atenção"
                   : root.status === "cancelled" ? "Interrompido" : "Falhou"
}
