"""Internal Name Editor"""

# import from other files
from AdvEditor import AdvWindow, Adv3Attr, Adv3Save
from AdvGame import GBA
from AdvGUI.GeneralQt import *

class QDialogInternalName(QDialogBase):
    "Dialog for editing the ROM's internal name."
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Edit Internal ROM Name")

        # init widgets
        self.lineedits = []
        for maxlength in (12, 4):
            self.lineedits.append(QLineEdit())
            self.lineedits[-1].setMaxLength(maxlength)
            self.lineedits[-1].setFixedWidth(maxlength*11 + 16)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addWidget(QLabel("Title (max 12 char)"))
        layoutMain[-1].addStretch()
        layoutMain[-1].addWidget(QLabel("ID (max 4 char)"))

        layoutMain.addRow()
        layoutMain[-1].addWidget(self.lineedits[0])
        layoutMain[-1].addWidget(self.lineedits[1])

        layoutMain.addAcceptRow(self, "Save")

        self.setFixedSize(self.sizeHint())

    def open(self):
        title, ID = GBA.readinternalname(Adv3Attr.filepath)
        self.lineedits[0].setText(title)
        self.lineedits[1].setText(ID)
        super().open()

    def accept(self):
        # convert strings to bytes, and add padding
        try:
            bytestowrite = bytearray(0x10)
            bytestowrite[0:len(self.lineedits[0].text())] = bytes(
                self.lineedits[0].text(), encoding="ASCII")
            bytestowrite[0xC:0xC+len(self.lineedits[1].text())] = bytes(
                self.lineedits[1].text(), encoding="ASCII")
        except UnicodeEncodeError:
            QSimpleDialog(self, title="Error", wordwrap=False,
                text="Only ASCII characters are allowed.").exec()
            return

        # update internal name
        Adv3Save.savewrapper(
            GBA.setinternalname, Adv3Attr.filepath, bytestowrite)

        # update status bar
        for i in range(0x10):
            if bytestowrite[i] == 0: bytestowrite[i] = 0x20
        AdvWindow.statusbar.setActionText(
            "Internal name changed to: " + str(bytestowrite, encoding="ASCII"))

        super().accept()
