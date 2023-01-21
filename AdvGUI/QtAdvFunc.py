"Misc Qt Functions"

# Qt imports
from .PyQtImport import QApplication, qRgb, QTimer

# import from other files
from AdvGame import AdvGame

def basewidth(widget):
    """Return a dynamic character width of the widget's font, used for
    cross-platform fixed widget widths."""
    return widget.fontMetrics().horizontalAdvance("_")

def color15toQRGB(color):
    "Convert a 15-bit RGB color to a 24-bit qRgb color."
    red, green, blue = AdvGame.color15to24(color)
    return qRgb(red, green, blue)

def createtogglefunc(widget):
    return lambda : widget.setVisible(not widget.isVisible())

def createdialogtogglefunc(dialog):
    def _togglefunc(checked):
        if checked:
            dialog.show()
        else:
            dialog.done(1)
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

def timerstart():
    "Start a one-shot timer."
    timer = QTimer()
    timer.setSingleShot(True)
    timer.start(1000000000)
    return timer

def timerend(timer):
    "Return time elapsed by a one-shot timer."
    return 1000000000 - timer.remainingTime()
