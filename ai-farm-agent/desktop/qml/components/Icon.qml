// Icone da fonte Segoe Fluent Icons (Windows 11). Passe o codepoint em
// `glyph`, ex.: "". Emojis e setas unicode renderizam diferente em
// cada maquina; a fonte de icones do sistema e consistente.
import QtQuick

Text {
    property string glyph: ""
    property int size: 16

    text: glyph
    color: Theme.textSecondary
    font.family: Theme.fontIcons
    font.pixelSize: size
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
    renderType: Text.NativeRendering
}
