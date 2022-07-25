# standard library imports
import math, os

# import from other files
from AdvGame import *
from .QtGeneral import *

# globals
import AdvSettings, Adv3Attr, Adv3Visual

# Old viewer, to be recoded

class QSMA3PaletteViewer(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Palette Viewer")

        layoutMain = QVBoxLayout()
        self.setLayout(layoutMain)

        sBGgradient = QHBoxLayout()
        layoutMain.addLayout(sBGgradient)
        sBGgradient.addWidget(QLabel("Background Gradient"))

        layoutMain.addWidget(QHorizLine())

        sPaletteGrid = QGridLayout()
        layoutMain.addLayout(sPaletteGrid)
        sPaletteGrid.addWidget(QLabel("<b>Layer Palettes</b>"), 0, 0,
            Qt.AlignmentFlag.AlignCenter)
        sPaletteGrid.addWidget(QLabel("<b>Sprite Palettes</b>"), 0, 2,
            Qt.AlignmentFlag.AlignCenter)
        sPaletteGrid.addWidget(QVertLine(), 0, 1, -1, 1)
        sLayerPaletteGrid = QGridLayout()
        sSpritePaletteGrid = QGridLayout()
        sPaletteGrid.addLayout(sLayerPaletteGrid, 1, 0)
        sPaletteGrid.addLayout(sSpritePaletteGrid, 1, 2)

        # add color boxes to layout
        self.colorwidgets = []
        for i in range(0x218):
            self.colorwidgets.append(QSMA3PaletteColor(0, colorID=i))

        for i in range(0x18):
            sBGgradient.addWidget(self.colorwidgets[i+0x200])
        sBGgradient.addStretch()
        for i in range(0x100):
            sLayerPaletteGrid.addWidget(self.colorwidgets[i],
                i//0x10, i%0x10 +1)
            sSpritePaletteGrid.addWidget(self.colorwidgets[i+0x100],
                i//0x10, i%0x10 +1)
        for i in range(0x10):
            sLayerPaletteGrid.addWidget(
                QLabel(format(i, "X")), i, 0, Qt.AlignmentFlag.AlignRight)
            sSpritePaletteGrid.addWidget(
                QLabel(format(i+0x10, "X")), i, 0, Qt.AlignmentFlag.AlignRight)

        layoutMain.addWidget(QHorizLine())

        sLower = QHBoxLayout()
        layoutMain.addLayout(sLower)

        # Is there a better way than this wrapper layout, to prevent sColorInfo
        # from centering?
        sColorInfo0 = QVBoxLayout()
        sLower.addLayout(sColorInfo0)
        sColorInfo = QHBoxLayout()
        sColorInfo0.addLayout(sColorInfo)
        self.currentcolor = QColorSquareLabel(0)
        sColorInfo.addWidget(self.currentcolor)
        self.colorinfo = QLabel("\n")
        self.colorinfo.setFixedWidth(230)
        sColorInfo.addWidget(self.colorinfo)
        sColorInfo0.addStretch()

        sLower.addWidget(QVertLine())

        # Set up palette selection dropdowns
        sDropdowns = QGridLayout()
        sLower.addLayout(sDropdowns)
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
                sDropdowns.addWidget(self.dropdowns[key], i, 0)
            else:
                sDropdowns.addWidget(self.dropdowns[key], i-4, 1)

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
        sDropdowns.addWidget(exportbutton, 3, 2)

        sLower.addStretch()


        # disable the not-yet-implemented Palette Animation
        self.dropdowns[0xB].setDisabled(True)

        # set static window size determined by layout
        self.setFixedSize(self.sizeHint())

    def closeEvent(self, event):
        AdvSettings.editor.actions["Toggle Palette"].setChecked(False)
        super().closeEvent(event)

    def updatePalette(self):
        """Update the active sublevel's header IDs, using the current settings
        of the dropdowns. Then reload this window's palette."""
        headertoupdate = {}
        for key in self.dropdowns:
            if key < len(SMA3.Constants.headersettings):
                if Adv3Attr.sublevel.header[key] !=\
                   self.dropdowns[key].currentIndex():
                    headertoupdate[key] = self.dropdowns[key].currentIndex()

        if headertoupdate:
            AdvSettings.editor.setHeader(headertoupdate)

    def updateYoshiPalette(self):
        AdvSettings.yoshipalID = self.dropdowns[0x48].currentIndex()
        Adv3Visual.palette.loadyoshipalette(
            Adv3Attr.filepath, AdvSettings.yoshipalID)
        AdvSettings.editor.reload("Sprite Graphics")
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
        red, green, blue = color15split(color)
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
        confirmbutton = QPushButton("Export")
        confirmbutton.clicked.connect(self.accept)
        confirmbutton.setDefault(True)
        cancelbutton = QPushButton("Cancel")
        cancelbutton.clicked.connect(self.reject)

        # init layout
        mainlayout = QVBoxLayout()
        self.setLayout(mainlayout)

        layoutrows = []
        for i in range(2):
            layoutrows.append(QHBoxLayout())
            mainlayout.addLayout(layoutrows[-1])
        layoutrows[0].addWidget(self.layersbutton)
        layoutrows[0].addWidget(self.spritesbutton)
        layoutrows[0].addStretch()
        layoutrows[1].addWidget(confirmbutton)
        layoutrows[1].addWidget(cancelbutton)

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
                for component in color15to24(color15):
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
        self.image.setColor(0, color15toQRGB(color))
        self.image.fill(0)

        if border:
            self.bordercolor = bordercolor
            self.image.setColor(1, color15toQRGB(bordercolor))

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
        self.image.setColor(0, color15toQRGB(color15bit))
        pixmap = QPixmap.fromImage(self.image)
        self.setPixmap(pixmap)

class QSMA3PaletteColor(QColorSquareLabel):
    """Subclass for representing a color in QSMA3PaletteViewer."""
    def __init__(self, *args, colorID=None):
        super().__init__(*args)
        self.colorID = colorID

    def enterEvent(self, *args):
        self.window().setColorinfo(self.color, self.colorID)
