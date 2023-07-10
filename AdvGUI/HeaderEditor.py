"""SMA3 Header Editor"""

# import from other files
import AdvEditor
from AdvEditor import AdvWindow, Adv3Attr, Adv3Patch, Adv3Sublevel
from AdvEditor.Number import hexstr_0tomax
from AdvGame import GBA, SMA3
from .GeneralQt import *

class QSMA3HeaderEditor(QDialogBase):
    "Dialog for editing the current sublevel's header settings."
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Edit Sublevel Header")

        self.header = None

        # init widgets
        self.labels = []
        self.lineeditbytes = []
        self.defaultlabeltext = []
        self.defaultmaxvalues = []
        self.defaulttooltips = []
        def _createupdatefunc(index):
            return lambda : self.updateheaderbyte(index)

        for i, setting in enumerate(SMA3.Constants.header):
            self.defaultmaxvalues.append(setting.maxvalue)

            text = f"{setting.name} {hexstr_0tomax(setting.maxvalue)}"
            self.defaultlabeltext.append(text)
            self.labels.append(QLabel(text))

            self.lineeditbytes.append(QLineEditHex(maxvalue=setting.maxvalue))
            if i == 0xC:
                self.lineeditbytes[i].editingFinished.connect(
                    self.headerlayer23callback)
            elif i == 0xD:
                self.lineeditbytes[i].editingFinished.connect(
                    self.headermusiccallback)
            self.lineeditbytes[i].editingFinished.connect(
                _createupdatefunc(i))

            self.defaulttooltips.append(setting.tooltip)
            self.labels[i].setToolTip(setting.tooltip)
            self.lineeditbytes[i].setToolTip(setting.tooltip)

        self.lineeditbytes[1].setMaxLength(2)  # allow for 2-digit tilesets

        tooltips = {
            "speed": ("""<i></i>How quickly the layer scrolls, relative to
layer 1. This is a fixed-point hex value: 0.80 means 1/2 speed, 0.40 means
1/4 speed."""),
            "initY": ("""<i></i>
Pixel offset to adjust the layer's Y position on screen."""),
            "initY_layer": ("""<i></i>
Pixel offset to adjust layer {layer}'s Y position on screen.<br>
Default: {default}"""),
            }

        self.layer23speedlabels = []
        for _ in range(4):
            label = QLabel()
            label.setToolTip(tooltips["speed"])
            self.layer23speedlabels.append(label)
        self.layer23lineedits = {}
        for layer in (2, 3):
            lineedit = QLineEditHex(maxvalue=0xFFFF)
            lineedit.setToolTip(tooltips["initY_layer"].format(
                layer=layer,
                default=f"{SMA3.Sublevel.layerYoffsets_defaults[layer]:04X}"))
            self.layer23lineedits[layer] = lineedit

        self.musiccheckbox = QCheckBox("Enable override")
        self.musiccheckbox.clicked.connect(self.enablemusicoverride)
        self.musicdropdown = QComboBox()
        self.musicdropdown.setToolTip(
            "Music Override [Advynia]<br>"
            "Customize the sublevel's music to any valid YI music ID.")
        for i, text in enumerate(SMA3.Constants.music):
            self.musicdropdown.addItem(f"{i:02X}: {text}")
        self.musicdropdown.setPlaceholderText("(invalid)")
        self.disableitemsbox = QCheckBox("Disable items")
        self.disableitemsbox.setToolTip(
            "Disable items [Advynia]<br>"
            "Disable use of pause menu items during this sublevel, "
            "regardless of music.")
        self.disableitemsbox.clicked.connect(self.disableitemscallback)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutGrid = QGridLayout()
        for text, column in (("<b>Graphics</b>", 0),
                             ("<b>Palette</b>", 10)):
            layoutGrid.addWidget(QLabel(text), 0, column, 1, 2,
                                 Qt.AlignmentFlag.AlignCenter)
        for i, (row, column) in enumerate((
             (1, 10), (2, 0), (2, 10), (3, 0), (3, 10), (4, 0), (4, 10), (5, 0),
             (5, 10), (None, 20), (6, 0), (6, 10), (None, 20), (None, 20), (None, 20))):
            if row is None: continue
            layoutGrid.addWidget(self.labels[i], row, column)
            layoutGrid.addWidget(self.lineeditbytes[i], row, column+1)

        layoutGrid.addWidget(QVertLine(), 0, 9, -1, 1)

        layoutMain.addRow()
        layoutMain[-1].addLayout(layoutGrid)
        layoutMain[-1].addStretch()
        layoutMain.addWidget(QLabel(
            "<i>Graphics/palette settings can also be adjusted in the "
            "8x8/Palette Viewers</i>"))
        layoutMain.addWidget(QHorizLine())

        layoutMain.addRow()

        layoutLayer23Sector = QVHBoxLayout()

        layoutLayer23Sector.addRow()
        layoutLayer23Sector[-1].addStretch()
        layoutLayer23Sector[-1].addWidget(QLabel("<b>Layer Scroll Settings</b>"))
        layoutLayer23Sector[-1].addStretch()

        layoutLayer23Sector.addRow()
        layoutLayer23Sector[-1].addWidget(self.labels[0xC])
        layoutLayer23Sector[-1].addSpacing(10)
        layoutLayer23Sector[-1].addWidget(self.lineeditbytes[0xC])
        layoutLayer23Sector[-1].addStretch()

        layoutLayer23Grid = QGridLayout()
        for text, row, column in (
                ("Layer 2", 1, 0), ("Layer 3", 2, 0),
                ("X speed", 0, 2), ("Y speed", 0, 3), 
                ("Initial Y", 0, 4),
                ):
            label = QLabel(text)
            if "speed" in text: label.setToolTip(tooltips["speed"])
            elif "Initial Y" in text: label.setToolTip(tooltips["initY"])
            layoutLayer23Grid.addWidget(label, row, column)
        for args in (
                (self.layer23speedlabels[0], 1, 2),
                (self.layer23speedlabels[1], 1, 3),
                (self.layer23speedlabels[2], 2, 2),
                (self.layer23speedlabels[3], 2, 3),
                (self.layer23lineedits[2], 1, 4),
                (self.layer23lineedits[3], 2, 4),
                ):
            layoutLayer23Grid.addWidget(*args, Qt.AlignmentFlag.AlignCenter)

        layoutLayer23Sector.addRow()
        layoutLayer23Sector[-1].addLayout(layoutLayer23Grid)
        layoutLayer23Sector.addStretch()

        layoutOtherSector = QGridLayout()
        layoutOtherSector.addWidget(QLabel("<b>Other</b>"), 0, 0, 1, -1,
                                    Qt.AlignmentFlag.AlignCenter)
        layoutOtherSector.addWidget(self.labels[0x9], 1, 0)
        layoutOtherSector.addWidget(self.lineeditbytes[0x9], 1, 1)
        layoutOtherSector.addWidget(self.labels[0xE], 2, 0)
        layoutOtherSector.addWidget(self.lineeditbytes[0xE], 2, 1)

        layoutOtherSectorAlign = QVBoxLayout()
        layoutOtherSectorAlign.addLayout(layoutOtherSector)
        layoutOtherSectorAlign.addStretch()

        layoutMain.addRow()
        layoutMain[-1].addLayout(layoutLayer23Sector)
        layoutMain[-1].addWidget(QVertLine())
        layoutMain[-1].addLayout(layoutOtherSectorAlign)
        layoutMain[-1].addStretch()

        layoutMain.addWidget(QHorizLine())

        layoutMusicSector = QGridLayout()

        layoutMusicSector.addWidget(QLabel("<b>Music</b>"), 0, 0)
        layoutHeaderMusic = QHBoxLayout()
        layoutHeaderMusic.addWidget(self.labels[0xD])
        layoutHeaderMusic.addSpacing(10)
        layoutHeaderMusic.addWidget(self.lineeditbytes[0xD])
        layoutHeaderMusic.addStretch(10)
        layoutMusicSector.addLayout(layoutHeaderMusic, 0, 2, 1, -1)

        layoutMusicSector.addWidget(self.musiccheckbox, 1, 0)
        layoutMusicSector.addWidget(self.musicdropdown, 1, 2)
        layoutMusicSector.addWidget(self.disableitemsbox, 1, 3)

        layoutMain.addLayout(layoutMusicSector)
        layoutMain.addWidget(QHorizLine())

        layoutMain.addAcceptRow(self)

        layoutMain.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def open(self):
        # update header copy
        self.header = Adv3Attr.sublevel.header.copy()
        for i, value in enumerate(self.header):
            self.lineeditbytes[i].setValue(value)

        # load layer 2/3 scroll speed tables from ROM
        layer23data = []
        musicIDdata = []
        with GBA.Open(Adv3Attr.filepath, "rb") as f:
            f.readseek(SMA3.Pointers.layer23speeds)
            for _ in range(4):
                newdata = []
                for _ in range(SMA3.Constants.header[0xC].maxvalue + 1):
                    newdata.append(f.readint(2))
                layer23data.append(newdata)

            f.readseek(SMA3.Pointers.headermusicIDs)
            musicIDdataraw = f.read(0x1C)
            f.readseek(SMA3.Pointers.headermusicitemflags)
            musicitemflagsraw = f.read(0x1C)
            for i in range(0, 0x1C, 2):
                musicIDdata.append(
                    (int.from_bytes(musicIDdataraw[i:i+2], "little"),
                     int.from_bytes(musicitemflagsraw[i:i+2], "little")))

        musicIDdata += [(-1, 0), (-1, 1)]  # unused vanilla IDs,
                                           #  repurposed for Advynia

        self.headerlists = {0xC: layer23data, 0xD: musicIDdata}

        # update displayed layer 2/3 values
        layerYoffsets = Adv3Attr.sublevel.layerYoffsets
        for key in layerYoffsets:
            self.layer23lineedits[key].setValue(layerYoffsets[key])
        self.headerlayer23callback()
        

        # account for music override
        enabled = False
        if Adv3Attr.musicoverride:
            enabled = (self.lineeditbytes[0xD].value > 0xD)
        if enabled:
            self.disableitemsbox.setChecked(
                self.lineeditbytes[0xD].value & 1)
            if Adv3Attr.sublevel.music is not None:
                self.musicdropdown.setCurrentIndex(Adv3Attr.sublevel.music)
            else:
                self.musicdropdown.setCurrentIndex(-1)
        else:
            self.headermusiccallback()
        self.musiccheckbox.setChecked(enabled)
        self.enablemusicoverride(enabled)

        super().open()

    def updateheaderbyte(self, index, value=None):
        if value is not None:
            self.lineeditbytes[index].setValue(value)
        self.header[index] = self.lineeditbytes[index].value

    def accept(self):
        # update any changed header settings, with appropriate callbacks
        toupdate = Adv3Sublevel.cmpheader(self.header)
        if toupdate:
            AdvWindow.editor.setHeader(toupdate)

        # update sublevel's layer 2/3 Y offsets
        layerYoffsets = Adv3Attr.sublevel.layerYoffsets
        for key in layerYoffsets:
            newvalue = self.layer23lineedits[key].value
            if layerYoffsets[key] != newvalue:
                layerYoffsets[key] = newvalue
                toupdate["Layer " + str(key) + " Offset"] = newvalue

        # account for music override
        if self.musiccheckbox.isChecked():
            newvalue = self.musicdropdown.currentIndex()
        else:
            newvalue = None
        if Adv3Attr.sublevel.music != newvalue:
            Adv3Attr.sublevel.music = newvalue
            toupdate["Music Override"] = newvalue

        if toupdate:
            setaction(toupdate)

        super().accept()

    def updatepatchlayout(self):
        if Adv3Attr.sublevelstripes:
            self.labels[7].setText("<i>Unused (00-FF)<i>")
            self.lineeditbytes[7].maxvalue = 0xFF
            tooltip = """<i>Unused</i><br>
Due to the Sublevel Sprite Tilesets patch, this header value is unused.
Editing it is only useful for custom purposes."""
            self.labels[7].setToolTip(tooltip)
            self.lineeditbytes[7].setToolTip(tooltip)
        else:
            self.labels[7].setText(self.defaultlabeltext[7])
            self.lineeditbytes[7].maxvalue = self.defaultmaxvalues[7]
            self.labels[7].setToolTip(self.defaulttooltips[7])
            self.lineeditbytes[7].setToolTip(self.defaulttooltips[7])

        if Adv3Attr.musicoverride:
            self.labels[0xD].setText(self.defaultlabeltext[0xD][:-2] + "D)")
        else:
            self.labels[0xD].setText(self.defaultlabeltext[0xD])

        if Adv3Attr.world6flag:
            self.labels[1].setText(self.defaultlabeltext[1][:-4] + "00-1F)")
            self.lineeditbytes[1].maxvalue = 0x1F
        else:
            self.labels[1].setText(self.defaultlabeltext[1])
            self.lineeditbytes[1].maxvalue = self.defaultmaxvalues[1]

    def headerlayer23callback(self):
        """Update layer 2/3 sector according to the current header setting.
        Called from editing lineeditbytes[0xC]."""
        headervalue = self.lineeditbytes[0xC].value

        for seq, label in zip(self.headerlists[0xC], self.layer23speedlabels,
                              strict=True):
            newvalue = seq[headervalue]
            if newvalue == 0xFFFF:
                newvalue = 0x100
            label.setText(f"{newvalue >> 8 :X}.{newvalue & 0xFF :02X}")

    def headermusiccallback(self):
        """Update music override sector according to the current header setting.
        Called during dialog open, and from editing lineeditbytes[0xD]."""
        newvalue = self.lineeditbytes[0xD].value
        if Adv3Attr.musicoverride and newvalue > 0xD and\
                not self.musiccheckbox.isChecked():
            self.updateheaderbyte(0xD, 0xD)
            newvalue = 0xD
        musicID, disableitems = self.headerlists[0xD][newvalue]
        self.musicdropdown.setCurrentIndex(musicID)
        self.disableitemsbox.setChecked(disableitems)

    def enablemusicoverride(self, enabled):
        """Change layout to enable or disable the music override.
        Called during dialog open, and when the music checkbox is clicked."""
        if enabled and not Adv3Attr.musicoverride:
            applied = Adv3Patch.applypatch("musicoverride")
            if not applied:
                self.musiccheckbox.setChecked(False)
                return

        self.labels[0xD].setDisabled(enabled)
        self.lineeditbytes[0xD].setDisabled(enabled)
        self.musicdropdown.setEnabled(enabled)
        self.disableitemsbox.setEnabled(enabled)

        if enabled:
            self.disableitemscallback(self.disableitemsbox.isChecked())
        elif Adv3Attr.musicoverride and self.lineeditbytes[0xD].value > 0xD:
            self.updateheaderbyte(0xD, 0)
            self.headermusiccallback()

    def disableitemscallback(self, enabled):
        """Update the overridden header music value, based on the value of
        the disable items checkbox."""
        headerID = 0xE | int(enabled)
        self.updateheaderbyte(0xD, headerID)

def setaction(headertoupdate, usemergeID=False):
    """Set the undo action and status bar action for a particular mapping of
    header settings to update."""
    mergeID = None
    if not headertoupdate:
        return
    elif len(headertoupdate) == 1:
        i = tuple(headertoupdate)[0]
        headername = (i if isinstance(i, str)
                      else SMA3.Constants.header[i].shortname)
        actionstr = "Edit " + headername
        if usemergeID:
            mergeID = "Header Value " + str(i)
        AdvWindow.statusbar.setActionText(
            headername.lower().capitalize() + " updated.")
    else:
        actionstr = "Edit Header"
        AdvWindow.statusbar.setActionText("Sublevel header updated.")
    AdvWindow.undohistory.addaction(
        actionstr, mergeID=mergeID, updateset={"Header"})
