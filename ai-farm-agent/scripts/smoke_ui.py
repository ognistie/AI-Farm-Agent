"""QML load/render check with a fixture bridge. No mic, hotkeys, API or user history."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_QUICK_BACKEND'] = 'software'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PySide6
DLL_DIRECTORY = os.add_dll_directory(str(Path(PySide6.__file__).parent)) if os.name == 'nt' else None
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QObject, QUrl, QEventLoop, QTimer
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from desktop.bridge import Bridge


def main():
    QQuickStyle.setStyle('Basic')
    app = QGuiApplication([])
    from desktop.main import _setup_fonts
    from PySide6.QtGui import QFontDatabase
    # Offscreen Windows lacks the native font discovery path. Load the installed OS font,
    # using the same family as the real entry point; no font is redistributed.
    for name in ('segoeui.ttf', 'SegoeIcons.ttf', 'segmdl2.ttf'):
        font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / name
        if font.exists():
            QFontDatabase.addApplicationFont(str(font))
    _setup_fonts(app)
    bridge = Bridge.__new__(Bridge)
    QObject.__init__(bridge)
    bridge._controller = SimpleNamespace(state={'running': False}, list_conversations=lambda: [],
                                         session=SimpleNamespace(id='qa-fixture'))
    bridge._running = False
    bridge._voice = bridge._window_mode = bridge._stop_hotkey = None
    # Override data slots in a derived fixture would lose Qt's meta-method binding; instead
    # data files are redirected before QML can request them.
    from desktop import history_store
    history_store.HISTORY_FILE = ROOT / 'memory' / 'test_tmp' / 'ui-empty-history.jsonl'
    history_store.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    history_store.HISTORY_FILE.write_text('', encoding='utf-8')
    engine, loop = QQmlApplicationEngine(), QEventLoop()
    errors = []
    engine.warnings.connect(lambda items: errors.extend(e.toString() for e in items))
    engine.objectCreated.connect(lambda *args: loop.quit())
    engine.rootContext().setContextProperty('Bridge', bridge)
    engine.addImportPath(str(ROOT / 'desktop' / 'qml'))
    engine.load(QUrl.fromLocalFile(str(ROOT / 'desktop' / 'qml' / 'Main.qml')))
    if not engine.rootObjects():
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
    if not engine.rootObjects():
        print('\n'.join(errors))
        return 1
    root = engine.rootObjects()[0]
    root.setProperty('splashActive', False)
    root.show()
    QTimer.singleShot(1500, loop.quit)
    loop.exec()
    image = root.grabWindow()
    screenshot = ROOT / 'memory' / 'ui-release.png'
    if image.isNull() or not image.save(str(screenshot)):
        print('QML loaded but rendering failed.')
        return 1
    if bridge.metaObject().indexOfMethod('approvePlan(bool,QString)') < 0:
        return 1
    print('QML loaded and rendered:', image.width(), image.height())
    if errors:
        print('\n'.join(errors))
    # Destroy windows while the context bridge is still alive, avoiding shutdown-only warnings.
    for window in app.topLevelWindows(): window.close()
    engine.deleteLater(); app.processEvents()
    return 0 if not errors else 1


if __name__ == '__main__': raise SystemExit(main())
