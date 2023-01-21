"""General Qt Subclasses
Qt subclasses that are general-purpose enough to not be in a more
specialized file."""

# standard library imports
import os, time

# Qt imports
from .PyQtImport import *

# import from other files
import AdvMetadata, AdvEditor.Number
from AdvEditor import AdvSettings, Adv3Attr
from . import QtAdvFunc

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

class QDialogBase(QDialog):
    "Base class for Advynia's QDialogs. Includes a dialog screenshot action."
    @staticmethod
    def screenshotwindow():
        window = QApplication.activeWindow()
        window.grab().save(os.path.join(
            os.path.dirname(Adv3Attr.filepath),
            window.windowTitle().replace(" ", "") + "-" +
            time.strftime("%y%m%d%H%M%S") + ".png"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.addAction(QDialogBase.screenshotwindowaction)
        except AttributeError:
            # create class screenshot action only once
            #  (action needs to be created after the app initializes)
            action = QAction()
            action.triggered.connect(self.screenshotwindow)
            action.setShortcut("Shift+F12")
            self.addAction(action)
            QDialogBase.screenshotwindowaction = action

class QSimpleDialog(QDialogBase):
    """Basic dialog with an OK button and possibly a don't-show-again checkbox.
    Often used for displaying error/warning prompts.

    dontshow: if included, displays the checkbox. This should be an AdvSettings
              attribute that, if True, displays the dialog.
    """
    def __init__(self, *args, text="", title="Error", wordwrap=True,
                 dontshow=None):
        super().__init__(*args)
        self.setWindowTitle(title)

        self.dontshow = dontshow

        # init widgets

        label = QLabel(text)
        label.setWordWrap(wordwrap)
        if dontshow is not None:
            self.checkbox = QCheckBox("Don't show this message again")

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(label)
        if dontshow is not None:
            layoutMain.addWidget(QHorizLine())
        layoutMain.addAcceptRow(self, rejectbutton=False)
        if dontshow is not None:
            layoutMain[-1].insertWidget(0, self.checkbox)

        self.setFixedSize(self.sizeHint())
        self.setMinimumWidth(QPushButton("OK").sizeHint().width() * 2)

    def accept(self):
        if self.dontshow is not None and self.checkbox.isChecked():
            setattr(AdvSettings, self.dontshow, False)  # disable warning
        super().accept()

class QSimpleDialog2(QDialogBase):
    "Basic dialog with accept/cancel buttons."
    def __init__(self, *args, text="", title="Error", wordwrap=True,
                 accepttext="OK", rejecttext="Cancel"):
        super().__init__(*args)
        self.setWindowTitle(title)

        # init widgets

        label = QLabel(text)
        label.setWordWrap(wordwrap)

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(label)
        layoutMain.addAcceptRow(self, accepttext, rejecttext)

        self.setFixedSize(self.sizeHint())

class QGraphicsViewTransparent(QGraphicsView):
    "QGraphicsView with a transparent background and added border."
    def __init__(self, *args):
        super().__init__(*args)
        self.setStyleSheet("background:transparent;")
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)

class QLabelToolTip(QLabel):
    """QLabel that updates its tooltip to match its text. Optionally adds a
    prefix to non-empty tooltips."""
    def __init__(self, *args, prefix=""):
        super().__init__(*args)
        self.prefix = prefix
        if args and isinstance(args[0], str):
            self.setToolTip(prefix + args[0])

    def setText(self, text):
        super().setText(text)
        if text:
            self.setToolTip(self.prefix + text)
        else:
            self.setToolTip("")

class QLineEditByte(QLineEdit):
    "QLineEdit displaying a single user-editable hex number."
    def __init__(self, *args, minvalue=0, maxvalue=0xFF):
        super().__init__(*args)
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.value = minvalue

        maxlength = AdvEditor.Number.hexlen(maxvalue)

        self.setFixedWidth(
            max(maxlength, 2) * self.fontMetrics().horizontalAdvance("D") + 9)
        self.setMaxLength(maxlength)
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
            self.editingFinished.emit()
            self.setValue(self.value + 1)
            self.editingFinished.emit()
        elif event.key() == Qt.Key.Key_Down:
            self.editingFinished.emit()
            self.setValue(self.value - 1)
            self.editingFinished.emit()
        else:
            super().keyPressEvent(event)

class QListWidgetResized(QListWidget):
    "QListWidget with a modified default size."
    def __init__(self, width=256, height=200, *args):
        super().__init__(*args)
        self.startwidth = width
        self.startheight = height

    def sizeHint(self):
        return QSize(self.startwidth, self.startheight)

class QPainterSource(QPainter):
    "QPainter that can overwrite pixels with transparent pixels."
    def __init__(self, *args):
        super().__init__(*args)
        self.setCompositionMode(self.CompositionMode.CompositionMode_Source)

class QPlainTextEdit(QPlainTextEdit):
    """Replacement of QPlainTextEdit to ensure copying includes newlines,
    not the default U+2029 character."""
    def createMimeDataFromSelection(self):
        data = super().createMimeDataFromSelection()
        text = data.text().replace("\u2029", "\n")
        data.setText(text)
        return data

class QTransparentPixmap(QPixmap):
    "QPixmap that's initialized to transparent."
    def __init__(self, width, height):
        super().__init__(width, height)
        self.fill(QColor(0, 0, 0, 0))

class QVHBoxLayout(QVBoxLayout):
    """QVBoxLayout with on-demand adding of QHBoxLayout rows, and sequence-like
    indexing for each row."""
    def __init__(self):
        super().__init__()
        self._list = []

    def __getattr__(self, name):
        return getattr(self._list, name)
    def __getitem__(self, key):
        return self._list.__getitem__(key)
    def __len__(self):
        return len(self._list)

    def addRow(self, stretch=0):
        "Add a new QHBoxLayout to the end of the layout."
        self._list.append(QHBoxLayout())
        self.addLayout(self[-1], stretch)

    def insertRow(self, i):
        """Insert a new QHBoxLayout at the specified position. This should only
        be used if the layout consists exclusively of rows, not widgets;
        otherwise self._list becomes desynced."""
        newlayout = QHBoxLayout()
        self._list.insert(i, newlayout)
        self.insertLayout(i, newlayout)

    def addAcceptRow(self, window, accepttext="OK", rejecttext="Cancel", *,
                     labeltext=None, acceptbutton=True, rejectbutton=True,
                     addattr=False):
        """Add a row containing right-aligned accept/reject buttons for the
        provided window, and set the accept button as default.
        Optionally include a left-aligned label."""

        self.addRow()
        if labeltext:
            self[-1].addWidget(QLabel(labeltext))
            self[-1].addSpacing(10)
        self[-1].addStretch()

        if acceptbutton:
            acceptbutton = QPushButton(accepttext)
            acceptbutton.clicked.connect(window.accept)
            acceptbutton.setDefault(True)
            self[-1].addWidget(acceptbutton)
            if addattr:
                window.acceptbutton = acceptbutton

        if rejectbutton:
            rejectbutton = QPushButton(rejecttext)
            rejectbutton.clicked.connect(window.reject)
            self[-1].addWidget(rejectbutton)
            if addattr:
                window.rejectbutton = rejectbutton

QSPIgnoreWidth = QSizePolicy(
    QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

# Graphics classes

class QAdvyniaIcon(QIcon):
    "QIcon of an image from Advynia's icons folder."
    def __init__(self, filename):
        super().__init__(os.path.join(AdvMetadata.datadir, "icon", filename))

class Q8x8Tile(QImage):
    "Base class for representing 8x8 tiles with 15-bit indexed color."
    def __init__(self):
        super().__init__(8, 8, QImage.Format.Format_Indexed8)
        self.fill(0)

    def setPalette(self, palette):
        self.setColorTable(QtAdvFunc.color15toQRGB(color) for color in palette)
        self.setColor(0, 0)   # color 0 is always transparent

class QGBA8x8Tile(Q8x8Tile):
    """A visual representation of single 8x8 tile, given its GBA 4bpp graphics
    and 0x10-byte palette."""
    def __init__(self, tile, paletterow=(0,)*0x10):
        super().__init__()
        self.setPalette(paletterow)
        if not tile:
            return

        pixelarray = self.bits().asarray(64)
        for i, byte in zip(range(0, 64, 2), tile, strict=True):
            pixelarray[i] = byte & 0xF
            pixelarray[i+1] = byte >> 4

class QNumberedTile16(QImage):
    """Image of a 16x16 square, circle, or other shape, containing a 4x7 hex
    number. Intended to provide compact numbered graphics."""
    def __init__(self, numstr, qcolor, shape="square", textcolorindex=3):
        super().__init__(16, 16, QImage.Format.Format_Indexed8)

        # colors: 0:transparent, 1:black, 2:colored, 3:white
        colortable = [0, 0xFF000000, qcolor, 0xFFFFFFFF]
        self.setColorTable(colortable)
        self.fill(2)

        filename = "16"+shape+".bin"
        try:
            self.setImage(AdvMetadata.datapath("font", filename))
        except FileNotFoundError:
            print("Image " + filename + " not found!")

        startY = 4
        if shape == "star":
            startY = 5
        self.dispnumstr(numstr, 1, startY, textcolorindex)

    def setImage(self, filepath):
        # read color indexes from an external file
        newpixels = open(filepath, "rb").read()
        pixelarray = self.bits().asarray(0x100)
        for i in range(0x100):
            pixelarray[i] = newpixels[i]

    def dispnumstr(self, numstr, startX, startY, textcolorindex=3):
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
                            pixelarray[16*y + x] = textcolorindex
                        x += 1
                    y += 1
                startX += 5
