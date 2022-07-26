"""SMA3 Palette Viewer"""

# standard library imports
import math, os

# import from other files
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Visual
from AdvGame import AdvGame, SMA3
from .GeneralQt import *
from . import QtAdvFunc, HeaderEditor

# Old viewer, to be recoded

class QSMA3PaletteViewer(QDialog):
    """Dialog for displaying the currently loaded palette, and adjusting
    related sublevel settings."""
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Palette Viewer")

        self.savedpos = None

        spacing = 4

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

        # Is there a better way than this wrapper layout, to prevent
        #  layoutColorInfo from centering?
        layoutColorInfo0 = QVBoxLayout()
        layoutMain[-1].addLayout(layoutColorInfo0)
        layoutColorInfo = QHBoxLayout()
        layoutColorInfo0.addLayout(layoutColorInfo)
        layoutColorInfo0.addStretch()

        self.currentcolor = QColorSquareLabel(0)
        layoutColorInfo.addWidget(self.currentcolor)
        self.colorinfo = QLabel("\n")
        self.colorinfo.setFixedWidth(QtAdvFunc.basewidth(self.colorinfo) * 45)
        layoutColorInfo.addWidget(self.colorinfo)

        layoutMain[-1].addWidget(QVertLine())

        # Set up palette selection dropdowns
        layoutDropdowns = QGridLayout()
        layoutMain[-1].addLayout(layoutDropdowns)
        self.dropdowns = {}
        dropdowninfo = list(((i, SMA3.Constants.headersettings[i],
                              SMA3.Constants.headermaxvalues[i])
                              for i in SMA3.Constants.headerpalettes))
        dropdowninfo.append((0x48, "Yoshi Palette", 7))
        # dropdown keys match header setting keys,
        #  except Yoshi Palette, which is not a header setting
        for i, (key, name, maxvalue) in enumerate(dropdowninfo):
            self.dropdowns[key] = QComboBox()
            if i < 4:
                layoutDropdowns.addWidget(self.dropdowns[key], i, 0)
            else:
                layoutDropdowns.addWidget(self.dropdowns[key], i-4, 1)

            for j in range(maxvalue+1):
                if maxvalue >= 0x10:
                    self.dropdowns[key].addItem(name + " " + format(j, "02X"))
                else:
                    self.dropdowns[key].addItem(name + " " + format(j, "X"))
            if key == 0x48:
                self.dropdowns[key].activated.connect(self.updateYoshiPalette)
            else:
                self.dropdowns[key].activated.connect(self.updatePalette)

        exportbutton = QPushButton("Export")
        exportbutton.clicked.connect(QDialogExportPalette(self).open)
        layoutDropdowns.addWidget(exportbutton, 3, 2)

        layoutMain[-1].addStretch()


        # disable the not-yet-implemented Palette Animation
        self.dropdowns[0xB].setDisabled(True)

        # set static window size determined by layout
        self.setFixedSize(self.sizeHint())

    def show(self):
        "Restore saved window position/size."
        if self.savedpos is None:
            self.setColorinfo(Adv3Visual.palette[0], 0)
        else:
            self.move(self.savedpos)
        super().show()

    def closeEvent(self, event):
        AdvWindow.editor.actions["Toggle Palette"].setChecked(False)
        self.savedpos = self.pos()
        self.close()

    def reject(self):
        "Overridden to prevent Esc from closing the dialog."
        pass

    def updatePalette(self):
        """Update the active sublevel's header IDs, using the current settings
        of the dropdowns. Then reload this window's palette."""
        headertoupdate = {}
        for key in self.dropdowns:
            if key < len(SMA3.Constants.headersettings):
                if (Adv3Attr.sublevel.header[key] !=
                        self.dropdowns[key].currentIndex()):
                    headertoupdate[key] = self.dropdowns[key].currentIndex()

        if headertoupdate:
            AdvWindow.editor.setHeader(headertoupdate)
            HeaderEditor.setaction(headertoupdate, usemergeID=True)

    def updateYoshiPalette(self):
        Adv3Visual.yoshipalID = self.dropdowns[0x48].currentIndex()
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

    def updateDropdowns(self):
        """Update dropdowns with the currently active sublevel's header
        settings."""
        for i in SMA3.Constants.headerpalettes:
            self.dropdowns[i].setCurrentIndex(Adv3Attr.sublevel.header[i])

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

class QDialogExportPalette(QDialog):
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

            with open(filepath, "wb") as f:
                f.write(output)
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
            rowlength = math.ceil(size/4)*4 
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
