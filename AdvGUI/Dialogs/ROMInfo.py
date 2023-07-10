"""ROM Info dialog"""

# standard library imports
import os

# import from other files
import AdvEditor
from AdvEditor import Adv3Attr, Adv3Patch
from AdvEditor.Number import megabytetext
from AdvGame import GBA
from AdvGUI.GeneralQt import *

class QDialogROMInfo(QDialogBase):
    "Dialog listing info about the current ROM."
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("ROM Info")

        # init widgets
        self.labels = {}
        for key in ("internalname", "savedversion", "freespace"):
            self.labels[key] = QLabel()
        self.calcbutton = QPushButton("Calculate")
        self.calcbutton.clicked.connect(self.calcfreespace)

        self.patchlabels = []
        for patchID, value in Adv3Patch.patches.items():
            self.patchlabels.append(
                (QLabel(value[0] + ":"), QLabel("<b>False<b>")))

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        for labeltext, labelkey in (
                ("Internal name/ID:", "internalname"),
                ("Last saved version:", "savedversion"),
                ("Available free space:", "freespace"),
                ):
            layoutMain.addRow()
            layoutMain[-1].addWidget(QLabel(labeltext))
            layoutMain[-1].addStretch()
            layoutMain[-1].addWidget(self.labels[labelkey])

            if labelkey == "freespace":
                self.labels[labelkey].hide()
                layoutMain[-1].addWidget(self.calcbutton)

        layoutMain.addWidget(QHorizLine())

        layoutMain.addWidget(QLabel("Applied Patches:"))
        layoutPatches = QVHBoxLayout()
        layoutMain.addLayout(layoutPatches)
        for i, (namelabel, statuslabel) in enumerate(self.patchlabels):
            layoutPatches.addRow()
            layoutPatches[-1].addWidget(namelabel)
            layoutPatches[-1].addStretch()
            layoutPatches[-1].addWidget(statuslabel)

        layoutMain.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def open(self):
        if not AdvEditor.ROM.exists(): return

        name, ID = GBA.readinternalname(Adv3Attr.filepath)
        if ID:  # pad title width
            name = name.ljust(0xC) + ID
        self.labels["internalname"].setText(name)
        self.labels["savedversion"].setText(str(Adv3Attr.savedversion))
        self.labels["freespace"].hide()
        self.calcbutton.show()

        for i, patchID in enumerate(Adv3Patch.patches):
            patchflag = getattr(Adv3Attr, patchID)
            if patchflag is None:
                patchflag = "Unknown"
            self.patchlabels[i][1].setText(str(patchflag))

        super().open()

    def calcfreespace(self):
        freespace = AdvEditor.ROM.totalfreespace(Adv3Attr.filepath)
        self.labels["freespace"].setText("{0}/{1} MiB".format(
            megabytetext(freespace),
            megabytetext(os.path.getsize(Adv3Attr.filepath) - 0x400000)
            ))

        self.calcbutton.hide()
        self.labels["freespace"].show()
