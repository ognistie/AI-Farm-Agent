// Abertura em janela propria por cima do app (que ja esta maximizado e pronto
// embaixo), na mesma area da janela maximizada. Ao entrar, so esta janela some
// num fade: nada muda de tamanho nem de posicao, entao nao ha quebra de imagem.
// O Python a posiciona e mostra (desktop/main.py).
import QtQuick
import QtQuick.Window

Window {
    id: splashWindow
    objectName: "splashWindow"

    property bool active: true
    signal finished()

    visible: false
    transientParent: null
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: Theme.splashBase
    title: "AI Farm Agent"

    Splash {
        objectName: "splash"
        // Ligado ao tamanho da janela (e nao ao contentItem): o Python define a
        // geometria antes de mostrar, e o contentItem pode ficar em 0x0
        width: splashWindow.width
        height: splashWindow.height
        visible: splashWindow.active
        fadeTarget: splashWindow
        onFinished: {
            splashWindow.close()
            splashWindow.finished()
        }
    }
}
