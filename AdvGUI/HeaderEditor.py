# import from other files
from AdvGame import SMA3
from .QtGeneral import *

# globals
import AdvSettings, Adv3Attr, Adv3Patch

class QSMA3HeaderEditor(QDialog):
    "Dialog for editing the current sublevel's header settings."
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Edit Sublevel Header")

        self.header = None
        self.music = None

        # init widgets
        self.labels = []
        self.lineeditbytes = []
        self.defaultlabeltext = []
        self.defaultmaxvalues = []
        def _createupdatefunc(index):
            return lambda : self.updateheaderbyte(index)

        for i, name in enumerate(SMA3.Constants.headersettings):
            maxvalue = SMA3.Constants.headermaxvalues[i]
            self.defaultmaxvalues.append(maxvalue)

            text = "".join((
                format(i, "X"), ": ", name, " (",
                "0"*len(format(maxvalue, "X")), "-", format(maxvalue, "X"), ")",
                ))
            self.defaultlabeltext.append(text)
            self.labels.append(QLabel(text))

            self.lineeditbytes.append(QLineEditByte(maxvalue=maxvalue))
            if i == 0xD:
                self.lineeditbytes[i].editingFinished.connect(
                    self.headermusiccallback)
            self.lineeditbytes[i].editingFinished.connect(
                _createupdatefunc(i))

        self.lineeditbytes[1].setMaxLength(2)  # allow for 2-digit tilesets

        self.musiccheckbox = QCheckBox("Enable override")
        self.musiccheckbox.clicked.connect(self.enablemusicoverride)
        self.musicdropdown = QComboBox()
        for i, text in enumerate(SMA3.Constants.music):
            self.musicdropdown.addItem("".join((
                format(i, "02X"), ": ", text)))
        self.musicdropdown.setPlaceholderText("(invalid)")
        self.disableitemsbox = QCheckBox("Disable items")
        self.disableitemsbox.setToolTip(
            "Disable use of pause menu items during this sublevel.")
        self.disableitemsbox.clicked.connect(self.disableitemscallback)

        confirmbutton = QPushButton("OK")
        confirmbutton.clicked.connect(self.accept)
        confirmbutton.setDefault(True)
        cancelbutton = QPushButton("Cancel")
        cancelbutton.clicked.connect(self.reject)

        # init layout
        layoutMain = QVBoxLayout()
        self.setLayout(layoutMain)

        layoutGrid = QGridLayout()
        layoutMain.addLayout(layoutGrid)
        for text, column in (("<b>Graphics</b>", 0),
                             ("<b>Palette</b>", 10),
                             ("<b>Other</b>", 20)):
            layoutGrid.addWidget(QLabel(text), 0, column, 1, 2,
                                 Qt.AlignmentFlag.AlignCenter)
        for i, (row, column) in enumerate((
             (1, 10), (2, 0), (2, 10), (3, 0), (3, 10), (4, 0), (4, 10), (5, 0),
             (5, 10), (2, 20), (6, 0), (6, 10), (3, 20), (4, 20), (5, 20))):
            layoutGrid.addWidget(self.labels[i], row, column)
            layoutGrid.addWidget(self.lineeditbytes[i], row, column+1)
          # Account for 2-line item memory label
        layoutGrid.addWidget(self.labels[0xE], 5, 20, 2, 1,
                             Qt.AlignmentFlag.AlignTop)

        layoutGrid.addWidget(QVertLine(), 0, 9, -1, 1)
        layoutGrid.addWidget(QVertLine(), 0, 19, -1, 1)
        layoutMain.addWidget(QHorizLine())

        layoutMusic = QHBoxLayout()
        layoutMain.addLayout(layoutMusic)
        layoutMusic.addWidget(QLabel("<b>Music</b>"),
                              alignment=Qt.AlignmentFlag.AlignCenter)
        layoutMusic.addSpacing(10)
        layoutMusic.addWidget(self.musiccheckbox)
        layoutMusic.addSpacing(10)
        layoutMusic.addWidget(self.musicdropdown)
        layoutMusic.addWidget(self.disableitemsbox)
        layoutMusic.addStretch()

        layoutMain.addWidget(QHorizLine())

        layoutButtons = QHBoxLayout()
        layoutMain.addLayout(layoutButtons)
        layoutButtons.addWidget(QLabel(
            "<i>Graphics/palette settings can also be adjusted in the "
            "8x8/Palette Viewers</i>"))
        layoutButtons.addStretch()
        layoutButtons.addWidget(confirmbutton)
        layoutButtons.addWidget(cancelbutton)

        layoutMain.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def open(self):
        # update header copy
        self.header = Adv3Attr.sublevel.header.copy()
        for i, value in enumerate(self.header):
            self.lineeditbytes[i].setValue(value)

        # account for music override
        enabled = False
        if Adv3Attr.musicoverride:
            enabled = self.lineeditbytes[0xD].value > 0xD
        self.musiccheckbox.setChecked(enabled)
        self.enablemusicoverride(enabled)
        if enabled:
            self.disableitemsbox.setChecked(
                self.lineeditbytes[0xD].value & 1)
            if Adv3Attr.sublevel.music is not None:
                self.musicdropdown.setCurrentIndex(Adv3Attr.sublevel.music)
            else:
                self.musicdropdown.setCurrentIndex(-1)
        else:
            self.headermusiccallback()

        super().open()

    def updateheaderbyte(self, index, value=None):
        if value is not None:
            self.lineeditbytes[index].setValue(value)
        self.header[index] = self.lineeditbytes[index].value

    def accept(self):
        # update any changed header settings, with appropriate callbacks
        toupdate = {}
        for i, new, old in zip(range(len(self.header)),
                            self.header, Adv3Attr.sublevel.header):
            if new != old:
                toupdate[i] = new
        if toupdate:
            AdvSettings.editor.setHeader(toupdate)
            AdvSettings.editor.statusbar.setActionText(
                "Sublevel header updated.")

        # account for music override
        if self.musiccheckbox.isChecked():
            Adv3Attr.sublevel.music = self.musicdropdown.currentIndex()
        else:
            Adv3Attr.sublevel.music = None

        super().accept()

    def updatepatchlayout(self):
        if Adv3Attr.sublevelstripes:
            self.labels[7].setText("7: <i>Unused (00-FF)<i>")
            self.lineeditbytes[7].maxvalue = 0xFF
            tooltip = (
                "<i></i>Due to the Sublevel Sprite Tilesets patch, this header "
                "value is unused. Editing it is only useful for custom purposes.")
            self.labels[7].setToolTip(tooltip)
            self.lineeditbytes[7].setToolTip(tooltip)
        else:
            self.labels[7].setText(self.defaultlabeltext[7])
            self.lineeditbytes[7].maxvalue = self.defaultmaxvalues[7]
            self.labels[7].setToolTip("")
            self.lineeditbytes[7].setToolTip("")

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

    def headermusiccallback(self):
        """Update music override sector according to the current header setting.
        Called during dialog open, and from editing lineeditbytes[0xD]."""
        newvalue = self.lineeditbytes[0xD].value
        if Adv3Attr.musicoverride and newvalue > 0xD and\
                not self.musiccheckbox.isChecked():
            self.updateheaderbyte(0xD, 0xD)
            newvalue = 0xD
        musicID, disableitems = SMA3.Constants.headermusicIDs[newvalue]
        self.musicdropdown.setCurrentIndex(musicID)
        self.disableitemsbox.setChecked(disableitems)

    def enablemusicoverride(self, enabled):
        """Change layout to enable or disable the music override.
        Called during dialog open, and when the music checkbox is clicked."""
        if enabled and not Adv3Attr.musicoverride:
            applied = Adv3Patch.applymusicoverride()
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

