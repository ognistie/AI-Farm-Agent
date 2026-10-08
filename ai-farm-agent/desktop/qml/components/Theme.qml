// Tokens visuais. Tema claro (como o filme de lancamento): superficies
// brancas, cinzas neutros, preto para a acao primaria e um azul de destaque
// (o mesmo do logo). Mude aqui e a UI inteira segue.
pragma Singleton
import QtQuick

QtObject {
    // ─── Superficies ────────────────────────────────────────────────
    readonly property color bgSidebar:   "#F7F7F8"
    readonly property color bgBase:      "#FFFFFF"
    readonly property color bgSurface:   "#FFFFFF"
    readonly property color bgSurfaceHi: "#F1F1F3"
    readonly property color bgHover:     Qt.rgba(0, 0, 0, 0.04)
    readonly property color bgPressed:   Qt.rgba(0, 0, 0, 0.07)
    readonly property color hairline:    Qt.rgba(0, 0, 0, 0.08)
    readonly property color hairlineHi:  Qt.rgba(0, 0, 0, 0.16)

    // ─── Texto (contraste AA sobre branco: 16.8 / 5.1 / 4.5) ────────
    readonly property color textPrimary:   "#1D1D1F"
    readonly property color textSecondary: "#6E6E73"
    readonly property color textTertiary:  "#76767B"
    readonly property color textInverse:   "#FFFFFF"

    // ─── Acao primaria, destaque e status ───────────────────────────
    readonly property color primary:   "#111112"
    readonly property color accent:    "#0A7CFF"
    readonly property color success:   "#28A745"
    readonly property color danger:    "#E5372B"
    readonly property color warning:   "#D97706"
    readonly property color info:      "#0A7CFF"

    // ─── Abertura (degrade do filme: pessego, laranja, lilas) ───────
    readonly property color splashBase:   "#FBF7F4"
    readonly property color splashPeach:  "#F8C3AE"
    readonly property color splashOrange: "#F9D29A"
    readonly property color splashLilac:  "#D7C6F4"

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
    readonly property int sizeHero: 34

    readonly property int durFast: 120
    readonly property int durNormal: 200
    readonly property int durSlow: 600

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
