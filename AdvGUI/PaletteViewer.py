"""SMA3 Palette Viewer"""

# standard library imports
import itertools, math, os

# import from other files
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Visual
from AdvGame import AdvGame, SMA3
from .GeneralQt import *
from . import QtAdvFunc, HeaderEditor


class QSMA3PaletteViewer(QDialogBase):
    """Dialog for displaying the currently loaded palette, and adjusting
    related sublevel settings."""
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Palette Viewer")

        self.queuedupdate = True
        self.savedpos = None

        spacing = 4

        ## need to rewrite to split init widgets/init layout, like other windows

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].setSpacing(spacing)
        layoutMain[-1].addWidget(QLabel("Background Gradient"))

        layoutMain.addWidget(QHorizLine())

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

        # color boxes
        self.colorwidgets = [QSMA3PaletteColor(0, colorID=i)
                             for i in range(0x218)]
        for i in range(0x18):
            layoutMain[0].addWidget(self.colorwidgets[i+0x200])
        layoutMain[0].addStretch()
        for i in range(0x100):
            r = i // 0x10 + 1
            c = i % 0x10 + 1
            layoutLayerPalette.addWidget(self.colorwidgets[i], r, c)
            layoutSpritePalette.addWidget(self.colorwidgets[i+0x100], r, c)

        # numeric labels
        labels = []
        font = QLabel().font()
        font.setPointSize(font.pointSize() - 1)
        for i in range(0x20):
            label = QLabel(format(i, "X"))
            label.setFont(font)
            labels.append(label)
        for i in range(0x10):
            layoutLayerPalette.addWidget(
                labels[i], i+1, 0, Qt.AlignmentFlag.AlignRight)
            layoutSpritePalette.addWidget(
                labels[i+0x10], i+1, 0, Qt.AlignmentFlag.AlignRight)

        layoutMain.addWidget(QHorizLine())

        layoutMain.addRow()

        # color info sector
        layoutColorInfo = QVHBoxLayout()
        layoutMain[-1].addLayout(layoutColorInfo)
        layoutColorInfo.addRow()
        layoutColorInfo.addStretch()

        self.currentcolor = QColorSquareLabel(0)
        layoutColorInfo[-1].addWidget(self.currentcolor)
        self.colorinfo = QLabel("\n")
        self.colorinfo.setFixedWidth(QtAdvFunc.basewidth(self.colorinfo) * 45)
        layoutColorInfo[-1].addWidget(self.colorinfo)

        exportbutton = QPushButton("Export")
        exportbutton.setAutoDefault(False)
        exportbutton.clicked.connect(QDialogExportPalette(self).open)
        layoutColorInfo.addRow()
        layoutColorInfo[-1].addWidget(exportbutton)
        layoutColorInfo[-1].addStretch()

        layoutMain[-1].addWidget(QVertLine())

        # header setting line edits/dropdowns
        layoutHeader = QVHBoxLayout()
        layoutMain[-1].addLayout(layoutHeader)
        layoutHeaderGrid = QGridLayout()
        layoutHeaderGrid.addWidget(QVertLine(), 0, 2, 3, 1)
        layoutPaletteAnim = QHBoxLayout()
        layoutHeader.addRow()
        layoutHeader[-1].addLayout(layoutHeaderGrid)
        layoutHeader[-1].addStretch()
        layoutHeader.addLayout(layoutPaletteAnim)

        labels = {}
        self.lineedits = {}
        self.dropdowns = {}
        headerinfo = list(
            (i, SMA3.Constants.headersettings[i],
             SMA3.Constants.headermaxvalues[i])
            for i in SMA3.Constants.headerpalettes)
        headerinfo.append((0x48, "Yoshi Palette (display)", 7))
        # widget keys match header setting keys,
        #  except Yoshi Palette, which is not a header setting
        for i, ((key, name, maxvalue), (x, y)) in enumerate(zip(
                headerinfo,
                ((0, 0), (0, 1), (0, 2), (3, 0), (3, 1), (None, None), (3, 2))
                )):
            if key == 0xB:
                labels[key] = QLabel(name + ":")
                self.dropdowns[key] = QComboBox()
                layoutPaletteAnim.addWidget(labels[key])
                layoutPaletteAnim.addWidget(self.dropdowns[key])
                layoutPaletteAnim.addStretch()
                for j in range(maxvalue+1):
                    self.dropdowns[key].addItem("".join((
                        format(j, "02X"), ": ",
                        SMA3.Constants.headernames[0xB][j])))
                self.dropdowns[key].activated.connect(self.updatePalette)
            else:
                labels[key] = QLabel("".join((
                    name, " ", AdvEditor.Number.hexstr_0tomax(maxvalue), ":"
                    )))
                self.lineedits[key] = QLineEditByte("0", maxvalue=maxvalue)
                layoutHeaderGrid.addWidget(labels[key], y, x)
                layoutHeaderGrid.addWidget(self.lineedits[key], y, x+1)
                if key == 0x48:
                    self.lineedits[key].editingFinished.connect(self.updateYoshiPalette)
                else:
                    self.lineedits[key].editingFinished.connect(self.updatePalette)

        layoutMain[-1].addStretch()

        # set static window size determined by layout
        self.setFixedSize(self.sizeHint())

    def show(self):
        "Restore saved window position/size."
        if self.savedpos is None:
            self.setColorinfo(Adv3Visual.palette[0], 0)
        else:
            self.move(self.savedpos)
        super().show()
        if self.queuedupdate:
            self.runqueuedupdate()
            self.queuedupdate = False

    def closeEvent(self, event):
        AdvWindow.editor.actions["Toggle Palette"].setChecked(False)
        self.savedpos = self.pos()
        self.close()

    def reject(self):
        "Overridden to prevent Esc from closing the dialog."
        pass

    def queueupdate(self):
        if not self.isVisible():
            self.queuedupdate = True
            return
        else:
            self.runqueuedupdate()

    def runqueuedupdate(self):
        self.updatefromsublevel()
        self.reloadPalette()

    def updatePalette(self):
        """Update the active sublevel's header IDs, using the current settings
        of the dropdowns. Then reload this window's palette."""
        headertoupdate = {}
        for key, widget in itertools.chain(
                self.lineedits.items(), self.dropdowns.items()):
            if key < len(SMA3.Constants.headersettings):
                value = (widget.value if isinstance(widget, QLineEditByte)
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
        AdvWindow.editor.reload("Sprite Graphics")
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
        for i in SMA3.Constants.headerpalettes:
            if i in self.dropdowns:
                self.dropdowns[i].setCurrentIndex(Adv3Attr.sublevel.header[i])
            else:
                self.lineedits[i].setValue(Adv3Attr.sublevel.header[i])

    def setColorinfo(self, color, colorID):
        """Update the layout region displaying the current color."""
        red, green, blue = AdvGame.color15split(color)
        if colorID >= 0x200:
            text = ["Gradient Color ", format(colorID-0x200, "02X"),
                         " (", Adv3Visual.palette.colortype[0], ")"]
        else:
            text = ["Color ", format(colorID, "03X"), " (",
                         Adv3Visual.palette.colortype[colorID], ")"]
        text += [":\n", format(color, "04X"),
                 " (R ", format(red, "02X"),
                 ", G ", format(green, "02X"),
                 ", B ", format(blue, "02X"), ")"]

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
        filename = "".join(
            ("Sublevel", format(Adv3Attr.sublevel.ID, "02X"), "-{paltype}.pal"))
        if self.layersbutton.isChecked():
            paletteslice = Adv3Visual.palette[0:0x100]
            filename = filename.format(paltype="Layers")
        elif self.spritesbutton.isChecked():
            paletteslice = Adv3Visual.palette[0x100:0x200]
            filename = filename.format(paltype="Sprites")
        else:
            # if somehow neither is checked, don't crash
            return

        defaultpath = os.path.join(os.path.dirname(Adv3Attr.filepath), filename)

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

            # Why are pixel rows padded to the next multiple of 4 bytes?
            rowlength = self.image.bytesPerLine()
            pixelarray = self.image.bits().asarray(size*rowlength)
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
