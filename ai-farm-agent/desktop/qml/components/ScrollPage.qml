// Area rolavel com coluna central de largura maxima. Barra de rolagem
// fina que aparece quando ha conteudo para rolar. Coloque o conteudo
// como filhos: eles vao dentro de uma ColumnLayout centralizada.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Flickable {
    id: root

    default property alias content: column.data
    property int maxWidth: Theme.contentMax
    property int sidePadding: Theme.sp5
    property int topPadding: Theme.sp6
    property int bottomPadding: Theme.sp6
    property alias spacing: column.spacing

    clip: true
    contentWidth: width
    contentHeight: column.implicitHeight + topPadding + bottomPadding
    boundsBehavior: Flickable.StopAtBounds
    flickableDirection: Flickable.VerticalFlick

    function scrollToEnd() {
        contentY = Math.max(0, contentHeight - height)
    }

    ColumnLayout {
        id: column
        y: root.topPadding
        x: Math.max(root.sidePadding, (root.width - width) / 2)
        width: Math.min(root.maxWidth, root.width - root.sidePadding * 2)
        spacing: Theme.sp4
    }

    ScrollBar.vertical: ScrollBar {
        policy: root.contentHeight > root.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
        width: 10
        contentItem: Rectangle {
            implicitWidth: 4
            radius: 2
            color: Theme.alpha(Theme.textPrimary, parent.pressed ? 0.35 : 0.18)
        }
    }
}
