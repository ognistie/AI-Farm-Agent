// Singleton de tokens — estetica Claude / Lanes.sh / Anthropic.
// Minimalismo extremo, teal vibrante como acento, roxo sutil secundario,
// fundo preto profundo, off-white para texto. Hairlines ultra-finas.
pragma Singleton
import QtQuick

QtObject {
    // ─── Superficies (preto profundo + vidro fume) ──────────────────
    readonly property color bgBase:      "#0A0A0B"   // preto profundo
    readonly property color bgSidebar:   "#0C0D0F"
    readonly property color bgTopbar:    "#0A0A0B"
    readonly property color bgSurface:   "#121316"   // card base
    readonly property color bgSurfaceHi: "#191B1F"   // hover / destaque
    readonly property color bgGlass:     "#13141880" // 50% para overlay
    readonly property color bgInput:     "#0E0F11"

    // Hairlines invisiveis ate o foco
    readonly property color hairline:    "#1C1E22"
    readonly property color hairlineHi:  "#26292E"

    // ─── Texto (off-white premium) ──────────────────────────────────
    readonly property color textPrimary:   "#EDEEF0"
    readonly property color textSecondary: "#8B8E96"
    readonly property color textMuted:     "#56595F"
    readonly property color textInverse:   "#0A0A0B"

    // ─── Acentos (teal vibrante + roxo sutil) ───────────────────────
    readonly property color accent:       "#2dd4bf"   // teal Anthropic-ish
    readonly property color accentDim:    "#0f766e"
    readonly property color accentSoft:   "#2dd4bf"   // = accent (usado com alpha)
    readonly property color cyan:         "#2dd4bf"   // mesmo teal
    readonly property color violet:       "#a78bfa"   // roxo sutil
    readonly property color amber:        "#fbbf24"
    readonly property color coral:        "#f87171"
    readonly property color info:         "#7dd3fc"   // azul claro discreto

    // ─── Status semantico ───────────────────────────────────────────
    readonly property color statusOnline:  "#2dd4bf"
    readonly property color statusIdle:    "#56595F"
    readonly property color statusRunning: "#a78bfa"
    readonly property color statusWaiting: "#fbbf24"
    readonly property color statusError:   "#f87171"

    // ─── Espacamento ────────────────────────────────────────────────
    readonly property int spXs:  4
    readonly property int spSm:  8
    readonly property int spMd:  12
    readonly property int spLg:  16
    readonly property int spXl:  24
    readonly property int spXxl: 32

    // ─── Raios ──────────────────────────────────────────────────────
    readonly property int rXs:   4
    readonly property int rSm:   8
    readonly property int rMd:   10
    readonly property int rLg:   14
    readonly property int rXl:   20
    readonly property int rPill: 999

    // ─── Tipografia (Geist-like) ────────────────────────────────────
    readonly property string fontSans:  "Inter"
    readonly property string fontMono:  "JetBrains Mono"

    readonly property int sizeMicro:  10
    readonly property int sizeXs:     11
    readonly property int sizeSm:     12
    readonly property int sizeMd:     13
    readonly property int sizeLg:     15
    readonly property int sizeXl:     18
    readonly property int sizeXxl:    22
    readonly property int sizeHero:   28
    readonly property int sizeDisplay: 34

    // ─── Helpers ────────────────────────────────────────────────────
    function agentColor(name) {
        const n = (name || "").toUpperCase()
        if (n === "MAESTRO") return violet
        if (n === "CODE")    return accent
        if (n === "DATA")    return info
        if (n === "WEB")     return cyan
        if (n === "DESKTOP") return amber
        if (n === "FILE")    return "#fb923c"
        if (n === "VISION")  return coral
        if (n === "MEMORY")  return textSecondary
        return textSecondary
    }

    function levelColor(level) {
        switch ((level || "").toUpperCase()) {
            case "ERROR":   return coral
            case "WARN":
            case "WARNING": return amber
            case "INFO":    return info
            case "SUCCESS": return accent
            case "DEBUG":   return textMuted
            default:        return textSecondary
        }
    }

    function statusColor(status) {
        switch ((status || "").toLowerCase()) {
            case "online":   return statusOnline
            case "running":  return statusRunning
            case "waiting":  return statusWaiting
            case "error":    return statusError
            case "idle":     return statusIdle
            default:         return textMuted
        }
    }

    function alpha(c, a) { return Qt.rgba(c.r, c.g, c.b, a) }
}
