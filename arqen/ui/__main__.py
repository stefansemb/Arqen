import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from arqen.config.paths import APP_ROOT
from arqen.config.settings import load_language, load_provider_config, load_workspace_root
from arqen.core.engine import ConversationEngine
from arqen.core.chat_tools import apply_chat_tool_limits
from arqen.providers.factory import create_provider
from arqen.tools.builtins import create_builtin_registry
from arqen.ui.strings import set_language
from arqen.ui.window import ArqenWindow


def _log_without_console() -> None:
    """Give output somewhere to go when Arqen starts without a console.

    Started from a shortcut (pythonw), ``sys.stdout`` and ``sys.stderr`` are
    None, and anything that writes to them fails: Whisper's download progress,
    library warnings.  The output goes to ``data/arqen.log`` instead, which is
    also where to look when something goes wrong.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return
    from arqen.config import paths

    try:
        log_path = paths.data_dir() / "arqen.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        import os

        log = open(os.devnull, "w", encoding="utf-8")
    sys.stdout = sys.stdout or log
    sys.stderr = sys.stderr or log


def main() -> None:
    _log_without_console()
    load_workspace_root()
    set_language(load_language())
    config = load_provider_config()
    engine = ConversationEngine(
        provider=create_provider(config),
        tools=create_builtin_registry(),
    )
    apply_chat_tool_limits(engine)
    if sys.platform == "win32":
        # Without its own id, Windows groups Arqen under Python in the taskbar
        # and shows Python's icon.
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Arqen.Arqen")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(APP_ROOT / "assets" / "arqen.ico")))
    window = ArqenWindow(engine, provider_label=config.name, profile_name=config.profile_name)
    window.show()
    def center_window() -> None:
        if getattr(window, "geometry_restored", False):
            return
        screen = window.screen() or app.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            frame = window.frameGeometry()
            x = area.center().x() - frame.width() // 2
            y = area.center().y() - frame.height() // 2
            x = max(area.left(), min(x, area.right() - frame.width() + 1))
            y = max(area.top(), min(y, area.bottom() - frame.height() + 1))
            window.move(x, y)
    QTimer.singleShot(250, center_window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
