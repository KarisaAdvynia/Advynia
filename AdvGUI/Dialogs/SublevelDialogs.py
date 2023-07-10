# standard library imports
import os, platform
from collections.abc import Iterable

# import from other files
import AdvMetadata, AdvEditor
from AdvEditor import AdvWindow, Adv3Attr, Adv3Patch, Adv3Sublevel, Adv3Save
from AdvEditor.Format import pluralize
from AdvGame import GBA, SMA3
from AdvGUI import PyQtImport
from AdvGUI.GeneralQt import *

class QDialogSelectSublevel(QDialogBase):
    "Base class for load/save sublevel dialogs."
    def __init__(self, parent, swap=False):
        super().__init__(parent)

        # init widgets
        self.input = QLineEditHex(
            maxvalue=SMA3.Constants.maxsublevelIDscreenexit)
        self.confirmbutton = QPushButton()
        self.confirmbutton.clicked.connect(self.accept)
        self.confirmbutton.setDefault(True)
        cancelbutton = QPushButton("Cancel")
        cancelbutton.clicked.connect(self.reject)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addWidget(QLabel("Sublevel ID (00-F5):"))
        layoutMain[-1].addWidget(self.input)
        if swap:
            layoutMain.addRow()
            self.buttons = {}
            for text in ("Overwrite", "Swap"):
                self.buttons[text] = QRadioButton(text)
                layoutMain[-1].addWidget(self.buttons[text])
            self.buttons["Overwrite"].setChecked(True)
        layoutMain.addRow()
        layoutMain[-1].addWidget(self.confirmbutton)
        layoutMain[-1].addWidget(cancelbutton)

        self.setFixedSize(self.sizeHint())

    def open(self):
        "Display current sublevel in input, and set input to active."
        sublevelID = Adv3Attr.sublevel.ID
        if sublevelID is None:
            sublevelID = 0
        self.input.setValue(sublevelID)
        self.input.setFocus()
        super().open()

    def errormessage(self):
        QSimpleDialog(self, text="Sublevels F6-FF are Bandit minigames. "
            "Screen exits can be set to these sublevels, but they cannot "
            "be edited directly.",
            title="Error").exec()

class QDialogLoadSublevel(QDialogSelectSublevel):
    "Dialog for loading a sublevel from the ROM."
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("Load Sublevel")

        self.confirmbutton.setText("Load")

    def open(self):
        if not Adv3Sublevel.savecheck():
            return
        super().open()

    def accept(self):
        "Load sublevel, only if the input is a valid sublevel ID."
        sublevelID = self.input.value
        if sublevelID > SMA3.Constants.maxsublevelID:
            self.errormessage()
            return

        self.sublevelID = sublevelID
        if not Adv3Sublevel.loadsublevelID(self.sublevelID):
            return
        super().accept()

class QDialogSaveSublevelAs(QDialogSelectSublevel):
    "Dialog for saving the current sublevel as a different ID."
    def __init__(self, *args):
        super().__init__(*args, swap=True)

        self.setWindowTitle("Save Sublevel As")

        self.confirmbutton.setText("Save")

        self.setFixedSize(self.sizeHint())

    def open(self):
        """Run parent code, but if the current sublevel was imported, disable
        the Swap button."""
        if Adv3Attr.sublevel.datablocks:
            self.buttons["Swap"].setEnabled(True)
        else:
            self.buttons["Swap"].setEnabled(False)
            self.buttons["Overwrite"].setChecked(True)
        super().open()

    def accept(self):
        """If the input is a valid sublevel ID: handle swapping if needed,
        then save sublevel."""
        newID = self.input.value
        if newID > SMA3.Constants.maxsublevelID:
            self.errormessage()
            return

        if self.buttons["Swap"].isChecked():
            if not Adv3Save.savewrapper(self._swap, newID):
                return

        Adv3Attr.sublevel.ID = newID
        if not Adv3Sublevel.savesublevel_action():
            return
        super().accept()

    def _swap(self, newID):
        # swap new ID's and old ID's pointers
        oldID = Adv3Attr.sublevel.ID
        if newID == oldID:
            QSimpleDialog(self, title="Error", wordwrap=False,
                text="Sublevel cannot be swapped with itself.").exec()
            return False

        # swap sublevel-indexed patch data
        tempsublevel = SMA3.Sublevel.importbyID(Adv3Attr.filepath, newID)
        Adv3Patch.loadsublevelpatchattr(tempsublevel)
        Adv3Save.savesublevelpatchattr(tempsublevel, oldID)

        with GBA.Open(Adv3Attr.filepath, "r+b") as f:
            for baseptr in (SMA3.Pointers.sublevelmainptrs,
                            SMA3.Pointers.sublevelspriteptrs):
                ptrtable = f.readptr(baseptr)
                oldptroffset = ptrtable + 4*oldID
                newptroffset = ptrtable + 4*newID

                f.seek(oldptroffset)
                oldptr = f.read(4)
                f.seek(newptroffset)
                newptr = f.read(4)

                f.seek(oldptroffset)
                f.write(newptr)
                f.seek(newptroffset)
                f.write(oldptr)
        return True

class QDialogClearSublevel(QDialogBase):
    "Dialog for clearing all or part of the currently loaded sublevel."
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Clear Sublevel")

        # init widgets
        self.checkboxes = {}
        for key in ("Objects", "Sprites", "Header", "Screen Exits"):
            checkbox = QCheckBox(key)
            self.checkboxes[key] = checkbox

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutGrid = QGridLayout()
        layoutMain.addLayout(layoutGrid)
        for i, checkbox in enumerate(self.checkboxes.values()):
            layoutGrid.addWidget(checkbox, i&1, i&2)

        layoutMain.addAcceptRow(self)

        self.setFixedSize(self.sizeHint())

    def open(self):
        for key in self.checkboxes:
            self.checkboxes[key].setChecked(key != "Header")
        super().open()

    def accept(self):
        clearlist = [key for key in self.checkboxes
                     if self.checkboxes[key].isChecked()]
        if not clearlist:
            super().accept()
            return

        updateset = {"Byte Text"}
        sublevel = Adv3Attr.sublevel

        if "Objects" in clearlist:
            AdvWindow.selection.setSelectedObjects(None)
            sublevel.objects.clear()
            updateset |= {"Objects"}
        if "Sprites" in clearlist:
            AdvWindow.selection.setSelectedSpriteItems(None)
            sublevel.sprites.clear()
            updateset |= {"Sprites"}
        if "Screen Exits" in clearlist:
            sublevel.exits.clear()
            updateset |= {"Screen Exits"}
        if "Header" in clearlist:
            updatedict = Adv3Sublevel.cmpheader(
                setting.default for setting in SMA3.Constants.header)
            AdvWindow.editor.setHeader(updatedict)
            sublevel.layerYoffsets.update(sublevel.layerYoffsets_defaults)
            updateset |= {"Header"}

        AdvWindow.statusbar.setActionText(
            "Cleared " + ", ".join(clearlist).lower() + ".")
        AdvWindow.undohistory.addaction(
            "Clear " + (clearlist[0] if len(clearlist) == 1 else "Sublevel"),
            updateset=updateset, reload=True)
        super().accept()
