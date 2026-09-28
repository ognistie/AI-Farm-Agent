// Tokens visuais. Neutros escuros, um unico destaque (branco para acoes
// primarias) e cores de status do sistema. Mude aqui e a UI inteira segue.
pragma Singleton
import QtQuick

QtObject {
    // ─── Superficies ────────────────────────────────────────────────
    readonly property color bgSidebar:   "#171717"
    readonly property color bgBase:      "#1E1E1F"
    readonly property color bgSurface:   "#262628"
    readonly property color bgSurfaceHi: "#2F2F32"
    readonly property color bgHover:     Qt.rgba(1, 1, 1, 0.05)
    readonly property color bgPressed:   Qt.rgba(1, 1, 1, 0.09)
    readonly property color hairline:    Qt.rgba(1, 1, 1, 0.08)
    readonly property color hairlineHi:  Qt.rgba(1, 1, 1, 0.16)

    // ─── Texto ──────────────────────────────────────────────────────
    readonly property color textPrimary:   "#ECECEC"
    readonly property color textSecondary: "#A1A1A6"
    readonly property color textTertiary:  "#6E6E73"
    readonly property color textInverse:   "#111112"

    // ─── Acao primaria e status ─────────────────────────────────────
    readonly property color primary:   "#ECECEC"
    readonly property color success:   "#30D158"
    readonly property color danger:    "#FF453A"
    readonly property color warning:   "#FF9F0A"
    readonly property color info:      "#64D2FF"

    // ─── Espacamento e raios ────────────────────────────────────────
    readonly property int sp1: 4
    readonly property int sp2: 8
    readonly property int sp3: 12
    readonly property int sp4: 16
    readonly property int sp5: 24
    readonly property int sp6: 32

    readonly property int rSm: 8
    readonly property int rMd: 12
    readonly property int rLg: 20

    // Largura maxima da coluna de leitura (tela de tarefa e historico)
    readonly property int contentMax: 760

    // ─── Tipografia ─────────────────────────────────────────────────
    readonly property string fontSans:    "Segoe UI Variable Text"
    readonly property string fontDisplay: "Segoe UI Variable Display"
    readonly property string fontMono:    "Cascadia Mono"
    readonly property string fontIcons:   "Segoe Fluent Icons"

    readonly property int sizeXs:   11
    readonly property int sizeSm:   12
    readonly property int sizeMd:   14
    readonly property int sizeLg:   16
    readonly property int sizeXl:   20
    readonly property int sizeHero: 28

    readonly property int durFast: 120
    readonly property int durNormal: 200

    function alpha(c, a) { return Qt.rgba(c.r, c.g, c.b, a) }

    // Nome amigavel do agente (o backend usa CODE, DATA, ...)
    function agentLabel(name) {
        switch ((name || "").toUpperCase()) {
            case "MAESTRO": return "Maestro"
            case "CODE":    return "Código"
            case "DATA":    return "Dados"
            case "WEB":     return "Web"
            case "DESKTOP": return "Desktop"
            case "FILE":    return "Arquivos"
            case "MEMORY":  return "Memória"
            case "SYSTEM":  return "Sistema"
            default:        return name || ""
        }
    }
}
