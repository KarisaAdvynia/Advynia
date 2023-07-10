"Misc Qt Functions"

# Qt imports
from .PyQtImport import Qt, QApplication, qRgb, QTimer

# import from other files
from AdvGame import color15to24

def basewidth(widget) -> int:
    """Return a dynamic character width of the widget's font, used for
    cross-platform fixed widget widths."""
    return widget.fontMetrics().horizontalAdvance("_")

def color15toQRGB(color: int) -> int:
    "Convert a 15-bit RGB color to a 24-bit qRgb color."
    return qRgb(*color15to24(color))

def createtogglefunc(widget):
    return lambda : widget.setVisible(not widget.isVisible())

def createdialogtogglefunc(dialog):
    def _togglefunc(checked):
        if checked:
            dialog.show()
        else:
            dialog.close()
    return _togglefunc

def protectedmoveresize(window, x, y, width, height):
    """Move and resize a window to the provided coordinates, but ensure
    the window is contained within the available screen area."""
    rect = QApplication.primaryScreen().availableGeometry()
    width = min(width, rect.width())
    height = min(height, rect.height())
    x = min(x, rect.width()-width)
    y = min(y, rect.height()-height)

    window.move(x, y)
    window.resize(width, height)

def timerstart() -> QTimer:
    "Start a one-shot timer, to measure intervals up to 100 seconds."
    timer = QTimer()
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.setSingleShot(True)
    timer.start(100000)
    return timer

def timerend(timer):
    "Return time elapsed by a one-shot timer."
    return 100000 - timer.remainingTime()
