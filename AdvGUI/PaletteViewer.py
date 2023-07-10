"""SMA3 Palette Viewer"""

# standard library imports
import itertools, math, os

# import from other files
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Visual
from AdvEditor.Number import hexstr_0tomax
import AdvGame
from AdvGame import SMA3
from .GeneralQt import *
from . import QtAdvFunc, HeaderEditor

class QSMA3PaletteViewer(QDialogViewerBase):
    """Dialog for displaying the currently loaded palette, and adjusting
    related sublevel settings."""

    actionkey = "Palette Viewer"

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Palette Viewer")

        self.queuedupdate = True
        self.savedpos = None

        spacing = 4

        # init widgets

        self.colorwidgets = [QSMA3PaletteColor(0, colorID=i)
                             for i in range(0x218)]

        rowlabels = []
        font = QLabel().font()
        font.setPointSize(font.pointSize() - 1)
        for i in range(0x20):
            label = QLabel(format(i, "X"))
            label.setFont(font)
            rowlabels.append(label)

        self.currentcolor = QColorSquareLabel(0)
        self.colorinfo = QLabel("\n")
        self.colorinfo.setFixedWidth(QtAdvFunc.basewidth(self.colorinfo) * 45)
        exportbutton = QPushButton("Export")
        exportbutton.setToolTip("""<i></i>
Export the layer or sprite colors to a .pal file.""")
        exportbutton.setAutoDefault(False)
        exportbutton.clicked.connect(QDialogExportPalette(self).open)

        # widget keys match header setting keys,
        #  except Yoshi Palette, which is not a header setting
        labels = {}
        self.lineedits = {}
        self.dropdowns = {}
        palettesettings = (
            SMA3.Constants.headerpalettes + [SMA3.Constants._HeaderSetting(
                "Yoshi Palette (display)", 0x48, maxvalue=7,
                tooltip="""Determines palette row 15, which is used by certain
sprites, such as morph bubbles. This setting is for Advynia display purposes
only; it isn't saved with the sublevel.""")])

        for setting in palettesettings:
            key = setting.index
            if key == 0xB:  # use dropdown for palette animation
                labeltext = setting.name + ":"
                self.dropdowns[key] = QComboBox()
                for j, name in enumerate(SMA3.Constants.header[key].names):
                    self.dropdowns[key].addItem(f"{j:02X}: {name}")
                self.dropdowns[key].activated.connect(self.updatePalette)
                self.dropdowns[key].setToolTip(setting.tooltip)
            else:  # use line edit
                labeltext = (f"{setting.name} {hexstr_0tomax(setting.maxvalue)}:")
                self.lineedits[key] = QLineEditHex(
                    "0", maxvalue=setting.maxvalue)
                self.lineedits[key].editingFinished.connect(
                    self.updateYoshiPalette if key == 0x48
                    else self.updatePalette)
                self.lineedits[key].setToolTip(setting.tooltip)
            labels[key] = QLabel(labeltext)
            labels[key].setToolTip(setting.tooltip)

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        # background gradient
        layoutMain.addRow()
        layoutMain[-1].setSpacing(spacing)
        layoutMain[-1].addWidget(QLabel("Background Gradient"))
        for i in range(0x18):
            layoutMain[0].addWidget(self.colorwidgets[i+0x200])
        layoutMain[0].addStretch()

        layoutMain.addWidget(QHorizLine())

        # layer/sprite palette grid
        layoutMain.addRow()
        layoutLayerPalette = QGridLayout()
        layoutSpritePalette = QGridLayout()
        layoutMain[-1].addLayout(layoutLayerPalette)
        layoutMain[-1].addWidget(QVertLine())
        layoutMain[-1].addLayout(layoutSpritePalette)
        layoutMain[-1].addStretch()

        layoutLayerPalette.addWidget(QLabel("<b>Layer Palettes</b>"),
            0, 0, 1, 0x11, Qt.AlignmentFlag.AlignCenter)
        layoutSpritePalette.addWidget(QLabel("<b>Sprite Palettes</b>"),
            0, 0, 1, 0x11, Qt.AlignmentFlag.AlignCenter)
        layoutLayerPalette.setSpacing(spacing)
        layoutSpritePalette.setSpacing(spacing)

        for i in range(0x10):
            layoutLayerPalette.addWidget(
                rowlabels[i], i+1, 0, Qt.AlignmentFlag.AlignRight)
            layoutSpritePalette.addWidget(
                rowlabels[i+0x10], i+1, 0, Qt.AlignmentFlag.AlignRight)

        for i in range(0x100):
            r = i // 0x10 + 1
            c = i % 0x10 + 1
            layoutLayerPalette.addWidget(self.colorwidgets[i], r, c)
            layoutSpritePalette.addWidget(self.colorwidgets[i+0x100], r, c)

        # below palette grid
        layoutMain.addWidget(QHorizLine())
        layoutMain.addRow()

        # color info sector
        layoutColorInfo = QVHBoxLayout()
        layoutMain[-1].addLayout(layoutColorInfo)

        layoutColorInfo.addRow()
        layoutColorInfo.addStretch()
        layoutColorInfo[-1].addWidget(self.currentcolor)
        layoutColorInfo[-1].addWidget(self.colorinfo)

        layoutColorInfo.addRow()
        layoutColorInfo[-1].addWidget(exportbutton)
        layoutColorInfo[-1].addStretch()

        layoutMain[-1].addWidget(QVertLine())

        # header setting line edits/dropdowns
        layoutHeader = QVHBoxLayout()
        layoutMain[-1].addLayout(layoutHeader)
        layoutHeaderGrid = QGridLayout()
        layoutHeaderGrid.addWidget(QVertLine(), 0, 2, -1, 1)
        layoutHeader.addLayout(layoutHeaderGrid)
        layoutHeader.addStretch()

        gridpos = {2: (0, 0), 4: (0, 1), 6: (0, 2), 0: (3, 0),
                   8: (3, 1), 0x48: (3, 2), 0xB: (None, None)}
        widgets = self.lineedits | self.dropdowns
        for key, (x, y) in gridpos.items():
            if x is None:  # give exclusive row
                layoutHeader.addRow()
                layoutHeader[-1].addWidget(labels[key])
                layoutHeader[-1].addWidget(widgets[key])
                layoutHeader[-1].addStretch()
            else:  # place in grid
                layoutHeaderGrid.addWidget(labels[key], y, x)
                layoutHeaderGrid.addWidget(widgets[key], y, x+1)

        layoutMain[-1].addStretch()

        # set static window size determined by layout
        self.setFixedSize(self.sizeHint())

    def show(self):
        if self.savedpos is None:
            self.setColorinfo(Adv3Visual.palette[0], 0)
        super().show()

    def runqueuedupdate(self):
        self.updatefromsublevel()
        self.reloadPalette()

    def updatePalette(self):
        """Update the active sublevel's header IDs, using the current settings
        of the dropdowns. Then reload this window's palette."""
        headertoupdate = {}
        for key, widget in itertools.chain(
                self.lineedits.items(), self.dropdowns.items()):
            if key < len(SMA3.Constants.header):
                value = (widget.value if isinstance(widget, QLineEditHex)
                         else widget.currentIndex())
                if (Adv3Attr.sublevel.header[key] != value):
                    headertoupdate[key] = value

        if headertoupdate:
            AdvWindow.editor.setHeader(headertoupdate)
            HeaderEditor.setaction(headertoupdate, usemergeID=True)

    def updateYoshiPalette(self):
        Adv3Visual.yoshipalID = self.lineedits[0x48].value
        Adv3Visual.palette.loadyoshipalette(
            Adv3Attr.filepath, Adv3Visual.yoshipalID)
        AdvWindow.editor.reload({"Sprite Graphics"})
        self.reloadPalette()

    def reloadPalette(self):
        """Display the active palette."""
        for i in range(0x200):
            self.colorwidgets[i].setColor(Adv3Visual.palette[i])
        for i in range(0x18):
            self.colorwidgets[i+0x200].setColor(Adv3Visual.palette.BGgradient[i])

    def updatefromsublevel(self):
        """Update header selector widgets with the currently active sublevel's
        header settings."""
        for setting in SMA3.Constants.headerpalettes:
            i = setting.index
            if i in self.dropdowns:
                self.dropdowns[i].setCurrentIndex(Adv3Attr.sublevel.header[i])
            else:
                self.lineedits[i].setValue(Adv3Attr.sublevel.header[i])

    def setColorinfo(self, color, colorID):
        """Update the layout region displaying the current color."""
        red, green, blue = AdvGame.color15split(color)
        if colorID >= 0x200:
            text = f"Gradient Color {colorID-0x200:02X} ({Adv3Visual.palette.colortype[0]})"
        else:
            text = f"Color {colorID:03X} ({Adv3Visual.palette.colortype[colorID]})"
        text += f":\n{color:04X} (R {red:02X}, G {green:02X}, B {blue:02X})"

        self.currentcolor.setColor(color)
        self.colorinfo.setText("".join(text))

class QDialogExportPalette(QDialogBase):
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("Export Palette")

        # init widgets
        self.layersbutton = QRadioButton("Layers")
        self.spritesbutton = QRadioButton("Sprites")
        self.layersbutton.setChecked(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addRow()
        layoutMain[-1].addWidget(self.layersbutton)
        layoutMain[-1].addWidget(self.spritesbutton)
        layoutMain[-1].addStretch()
        layoutMain.addAcceptRow(self, "Export")

        self.setFixedSize(self.sizeHint())

    def accept(self):
        if self.layersbutton.isChecked():
            paletteslice = Adv3Visual.palette[0:0x100]
            paltype = "Layers"
        elif self.spritesbutton.isChecked():
            paletteslice = Adv3Visual.palette[0x100:0x200]
            paltype = "Sprites"
        else:
            # if somehow neither is checked, don't crash
            return

        defaultpath = os.path.join(os.path.dirname(Adv3Attr.filepath),
            f"Sublevel{Adv3Attr.sublevel.ID:02X}-{paltype}.pal")

        filepath, _ = QFileDialog.getSaveFileName(
            self, caption="Save Palette File", filter="Palette File (*.pal)",
            directory=defaultpath)
        if filepath:
            output = bytearray()
            for color15 in paletteslice:
                for component in AdvGame.color15to24(color15):
                    output.append(component)

            open(filepath, "wb").write(output)
            super().accept()

class QColorSquareLabel(QLabel):
    """Used for displaying a single 15-bit-color square box graphic,
    outside a graphics scene. Includes a black border by default."""
    def __init__(self, color, *args, size=14,
                 border=True, bordercolor=0):
        super().__init__(*args)
        self.image = QImage(size, size, QImage.Format.Format_Indexed8)
        self.image.setColor(0, QtAdvFunc.color15toQRGB(color))
        self.image.fill(0)

        if border:
            self.bordercolor = bordercolor
            self.image.setColor(1, QtAdvFunc.color15toQRGB(bordercolor))

            rowlength = self.image.bytesPerLine()
            pixelarray = self.image.bits().asarray(self.image.sizeInBytes())
            for i in range(size):
                pixelarray[i] = 1  # first row
                pixelarray[rowlength*(size-1) + i] = 1  # last row
                pixelarray[rowlength*i] = 1  # first column
                pixelarray[rowlength*i + size - 1] = 1  # last column
        self.setColor(color)

    def setColor(self, color15bit):
        self.color = color15bit
        self.image.setColor(0, QtAdvFunc.color15toQRGB(color15bit))
        pixmap = QPixmap.fromImage(self.image)
        self.setPixmap(pixmap)

class QSMA3PaletteColor(QColorSquareLabel):
    """Subclass for representing a color in QSMA3PaletteViewer."""
    def __init__(self, *args, colorID=None):
        super().__init__(*args)
        self.colorID = colorID

    def enterEvent(self, *args):
        self.window().setColorinfo(self.color, self.colorID)
