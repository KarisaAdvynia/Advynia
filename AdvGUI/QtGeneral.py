# standard library imports
import os

# Qt imports
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# import from other files
import AdvMetadata
from AdvGame import color15to24

# Misc Qt classes

class QHorizLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)

class QVertLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Plain)

class QLineEditByte(QLineEdit):
    def __init__(self, *args, minvalue=0, maxvalue=0xFF):
        super().__init__(*args)
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.value = minvalue

        self.setFixedWidth(25)
        self.setMaxLength(len(format(maxvalue, "X")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setValidator(QRegularExpressionValidator(QRegularExpression(
            "([0-9]|[A-F]|[a-f])+")))

        # apply maximum value
        self.editingFinished.connect(
            lambda : self.setValue(int(self.text(), base=16)))

    def setValue(self, value):
        if value > self.maxvalue:
            self.value = self.maxvalue
        elif value < self.minvalue:
            self.value = self.minvalue
        else:
            self.value = value
        self.setText(format(self.value, "0"+str(self.maxLength())+"X"))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.setValue(self.value + 1)
            self.editingFinished.emit()
        elif event.key() == Qt.Key.Key_Down:
            self.setValue(self.value - 1)
            self.editingFinished.emit()
        else:
            super().keyPressEvent(event)

class QPainterSource(QPainter):
    "QPainter subclass that can overwrite pixels with transparent pixels."
    def __init__(self, *args):
        super().__init__(*args)
        self.setCompositionMode(self.CompositionMode.CompositionMode_Source)

class QTransparentPixmap(QPixmap):
    "QPixmap subclass that's initialized to transparent."
    def __init__(self, width, height):
        super().__init__(width, height)
        self.fill(QColor(0, 0, 0, 0))

class QListWidgetResized(QListWidget):
    "QListWidget subclass with a modified default size."
    def __init__(self, width=256, height=200, *args):
        super().__init__(*args)
        self.startwidth = width
        self.startheight = height

    def sizeHint(self):
        return QSize(self.startwidth, self.startheight)

class QSimpleDialog(QMessageBox):
    """Basic dialog with only an OK button, often used for displaying
    error/warning prompts."""
    def __init__(self, *args, text="", title="Error"):
        super().__init__(*args)
        self.setWindowTitle(title)
        self.setText(text)

# Graphics classes

class QAdvyniaIcon(QIcon):
    "QIcon of an image from Advynia's icons folder."
    def __init__(self, filename):
        super().__init__(os.path.join(AdvMetadata.datadir, "icon", filename))

class Q8x8Tile(QImage):
    def __init__(self, *args):
        super().__init__(*args)

        self.fill(0)

    def setPalette(self, palette):
        for i, color in enumerate(palette):
            self.setColor(i, color15toQRGB(color))
        self.setColor(0, 0)   # color 0 is always transparent

class QGBA8x8Tile(Q8x8Tile):
    """A visual representation of single 8x8 tile, given its GBA 4bpp graphics
    and 0x10-byte palette."""
    def __init__(self, tile, paletterow=None):
        super().__init__(8, 8, QImage.Format.Format_Indexed8)
        if not paletterow:
            paletterow = [0]*0x10
        self.setPalette(paletterow)

        if not tile:
            return

        pixelarray = self.bits().asarray(64)
        index = 0
        for byte in tile:
            pixelarray[index] = byte&0xF
            pixelarray[index+1] = byte>>4
            index += 2

class QNumberedTile16(QImage):
    """Image of a 16x16 square, circle, or other shape, containing a 4x7 hex
    number. Intended to provide compact numbered graphics."""
    def __init__(self, numstr, qcolor, shape="square"):
        super().__init__(16, 16, QImage.Format.Format_Indexed8)

        # colors: 0:transparent, 1:black, 2:colored, 3:white
        colortable = [0, 0xFF000000, qcolor, 0xFFFFFFFF]
        self.setColorTable(colortable)
        self.fill(2)

        if shape=="circle":
            self.setImage(AdvMetadata.datapath("font", "16circle.bin"))
        elif shape=="octagon":
            self.setImage(AdvMetadata.datapath("font", "16octagon.bin"))
        else:  # default to square
            self.setImage(AdvMetadata.datapath("font", "16square.bin"))

        self.dispnumstr(numstr, 1, 4)

    def setImage(self, filepath):
        with open(filepath, "rb") as bitmap:
            newpixels = bitmap.read()
        pixelarray = self.bits().asarray(16*16)
        for i in range(0x100):
            pixelarray[i] = newpixels[i]

    def dispnumstr(self, numstr, startX, startY):
        if len(numstr) > 3:
            raise ValueError(
                'Insufficient space to display string "' + numstr + '".')
        elif len(numstr) == 0:
            return
        else:
            startX += (None, 5, 2, 0)[len(numstr)]
        
        pixelarray = self.bits().asarray(0x100)
        with open(AdvMetadata.datapath("font", "5x8font.bin"), "rb") as bitmap:
            for char in bytes(numstr, encoding="ASCII"):
                bitmap.seek(char*8)

                y = startY
                # shorten loop since digits fit in 4x7
                for byte in bitmap.read(7):
                    x = startX
                    for bitindex in range(4):
                        bit = (byte >> (7-bitindex)) & 1
                        if bit:
                            pixelarray[16*y + x] = 3
                        x += 1
                    y += 1
                startX += 5

# Misc functions

def color15toQRGB(color):
    "Convert a 15-bit RGB color to a 24-bit qRgb color."
    red, green, blue = color15to24(color)
    return qRgb(red, green, blue)

def keydirection(qkey):
    "Convert a QKey code for an arrow key into (x, y) displacement."
    if 16777234 <= qkey < 16777238:
        return ((+1, 0), (0, +1), (-1, 0), (0, -1))[qkey&3]

def timerstart():
    "Start a one-shot timer."
    timer = QTimer()
    timer.setSingleShot(True)
    timer.start(1000000000)
    return timer

def timerend(timer):
    "Return time elapsed by a one-shot timer."
    return 1000000000 - timer.remainingTime()
