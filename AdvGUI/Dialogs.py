"""Dialogs
Various minor dialog subclasses without enough code to receive their own
module."""

# standard library imports
import platform

# import from other files
import AdvMetadata, AdvEditor.ROM
from AdvEditor import AdvWindow, Adv3Attr, Adv3Patch, Adv3Sublevel, Adv3Save
from AdvGame import GBA, SMA3
from . import PyQtImport
from .GeneralQt import *

class QDialogAbout(QDialog):
    "Dialog for describing the editor."

    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("About Advynia")

        # init widgets
        advyniaicon = QLabel()
        advyniaicon.setPixmap(QPixmap(
            AdvMetadata.datapath("icon", "Advynia3.png")))
        advynianame = QLabel("".join((
            "<b>", AdvMetadata.appnamefull, "</b>")))
        advynianame.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        advyniadesc = QLabel("<br>".join((
            "(Python " + platform.python_version() +
            ", PyQt " + PyQtImport.PYQT_VERSION_STR + ")<hr>",
            AdvMetadata.aboutadvynia,
            )))
        advyniadesc.setTextFormat(Qt.TextFormat.RichText)
        advyniadesc.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        advyniadesc.setWordWrap(True)

        licensebutton = QPushButton("License Info")
        licensebutton.clicked.connect(QDialogLicenseInfo(self).exec)
        confirmbutton = QPushButton("OK")
        confirmbutton.clicked.connect(self.accept)
        confirmbutton.setDefault(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addWidget(advyniaicon)
        layoutMain[-1].addWidget(advynianame)
        layoutMain[-1].addStretch()

        layoutMain.addWidget(advyniadesc)

        layoutMain.addRow()
        layoutMain[-1].addStretch()
        layoutMain[-1].addWidget(licensebutton)
        layoutMain[-1].addWidget(confirmbutton)

    def open(self):
        self.setFocus()
        super().open()

class QDialogLicenseInfo(QDialog):
    "Dialog for displaying GPL license notes."

    gpltext = '''
This program is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version. 
<br><br>
This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details. 
<br><br>
You should have received a copy of the GNU General Public License along with 
this program.  If not, see 
<a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>'''

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("GNU General Public License")

        # init widgets
        label = QLabel(self.gpltext)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        label.setWordWrap(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(label)
        layoutMain.addAcceptRow(self, rejectbutton=False)


class QDialogROMValidation(QMessageBox):
    "Dialog for displaying errors/warnings when loading a ROM."
    def __init__(self, parent, size=None, crc32=None, savedversion=None,
                 override=True):
        super().__init__(parent)

        if savedversion is not None:
            text = [
                "This hack was created in Advynia ", str(savedversion),
                ". You are using version ", str(AdvMetadata.version), "."
                ]
        elif size is not None:
            text = [
                "File did not validate as a clean SMA3 (U) ROM image.\n"
                "Expected file size: 4194304 bytes\n"
                "Detected file size: ", str(size), " bytes"
                ]
        elif crc32 is not None:
            text = [
                "File did not validate as a clean SMA3 (U) ROM image.\n"
                "Expected CRC-32: 40A48276\n"
                "Detected CRC-32: ", format(crc32, "08X")
                ]

        if override:
            self.setWindowTitle("Warning")
            text.append("\n\nTry to load anyway?")
            self.addButton("Load", self.ButtonRole.AcceptRole)
            self.addButton("Cancel", self.ButtonRole.RejectRole)
        else:
            self.setWindowTitle("Error")
            self.addButton("OK", self.ButtonRole.RejectRole)

        self.setText("".join(text))

class QDialogSaveValidation(QMessageBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Warning")
        self.setText("This ROM has not yet been modified. Are you sure?")
        self.addButton("Save", self.ButtonRole.AcceptRole)
        self.addButton("Cancel", self.ButtonRole.RejectRole)

class QDialogPatchValidation(QDialog):
    "Dialog for warning the user that a patch is about to be applied."
    def __init__(self, name, desc):
        super().__init__(AdvWindow.editor)

        self.setWindowTitle("Patch Notice")

        text = """<b>{name}</b><br>{desc}"""
        label = QLabel(text.format(name=name, desc=desc))
        label.setWordWrap(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(label)
        layoutMain.addWidget(QHorizLine())

        layoutMain.addAcceptRow(self, "Apply",
            labeltext="<i>Applied patches can't be reverted!</i>")

        self.setFixedSize(self.sizeHint())

class QDialogImportPatch(QDialog):
    def __init__(self, patchlist, sublevel):
        super().__init__(AdvWindow.editor)

        self.setWindowTitle("Patch Notice")

        self.patchlist = patchlist
        self.sublevel = sublevel

        # init widgets
        warninglabel = QLabel("This sublevel uses Advynia patches that are not "
            "applied to the current ROM:")
        warninglabel.setWordWrap(True)

        patchtext = []
        for patchID in patchlist:
            patchtext.append(Adv3Patch.patches[patchID][0])
        patchtext = "".join(("<b>", "<br>".join(patchtext), "</b>"))
        patchlabel = QLabel(patchtext)

        self.radiobuttons = [
            QRadioButton("Apply patches"),
            QRadioButton("Import without patches (may break!)")]
        self.radiobuttons[0].setChecked(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(warninglabel)
        layoutMain.addWidget(patchlabel)
        for button in self.radiobuttons:
            layoutMain.addWidget(button)
        layoutMain.addWidget(QHorizLine())

        layoutMain.addAcceptRow(self, "Apply",
            labeltext="<i>Applied patches can't be reverted!</i>")

        self.setFixedSize(self.sizeHint())

    def accept(self):
        if self.radiobuttons[0].isChecked():
            Adv3Patch.applymultiplepatches(self.patchlist)
        else:
            if "musicoverride" in self.patchlist:
                self.sublevel.music = None
            if "object65" in self.patchlist:
                for obj in self.sublevel.objects:
                    if obj.ID == 0x65:
                        # convert into a stone block
                        obj.ID = 0x6C
                        obj.extID = None
            if "sublevelstripes" in self.patchlist:
                self.sublevel.stripeIDs = None
            if "world6flag" in self.patchlist:
                self.sublevel.header[1] &= 0xF
        super().accept()

class QDialogSelectSublevel(QDialog):
    "Base class for load/save sublevel dialogs."
    def __init__(self, parent, swap=False):
        super().__init__(parent)

        # init widgets
        self.input = QLineEditByte(
            maxvalue=SMA3.Constants.maxsublevelscreenexit)
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
        self.input.setText(format(sublevelID, "02X"))
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
        if sublevelID > SMA3.Constants.maxsublevel:
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
        if newID > SMA3.Constants.maxsublevel:
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
            QSimpleDialog(self, title="Error",
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

class QDialogClearSublevel(QDialog):
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
        updateset = set()

        if "Objects" in clearlist:
            AdvWindow.selection.setSelectedObjects(None)
            Adv3Attr.sublevel.objects.clear()
            updateset |= {"Objects"}
        if "Sprites" in clearlist:
            AdvWindow.selection.setSelectedSpriteItems(None)
            Adv3Attr.sublevel.sprites.clear()
            updateset |= {"Sprites"}
        if "Screen Exits" in clearlist:
            Adv3Attr.sublevel.exits.clear()
            updateset |= {"Screen Exits"}
        if "Header" in clearlist:
            updatedict = {}
            for i in range(len(Adv3Attr.sublevel.header)):
                updatedict[i] = SMA3.Constants.headerdefaults[i]
            AdvWindow.editor.setHeader(updatedict)
            updateset |= {"Header"}

        AdvWindow.statusbar.setActionText(
            "Cleared " + ", ".join(clearlist).lower() + ".")
        AdvWindow.statusbar.updateByteText()
        AdvWindow.undohistory.addaction(
            "Clear " + (clearlist[0] if len(clearlist) == 1 else "Sublevel"),
            updateset=updateset, reload=True)
        super().accept()

class QDialogSaveWarning(QDialog):
    """Dialog for prompting to save unsaved changes.
    Output: 1=Save, 0=Don't Save, 2=Cancel"""
    def __init__(self, *args,
            text="Would you like to save this sublevel before closing?"):
        super().__init__(*args)

        self.setWindowTitle("Unsaved Changes")

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(QLabel(text))
        layoutMain.addAcceptRow(
            self, accepttext="Save", rejecttext="Cancel")

        thirdbutton = QPushButton("Don't Save")
        thirdbutton.clicked.connect(lambda : self.done(2))
        layoutMain[-1].insertWidget(2, thirdbutton)

class QDialogROMInfo(QDialog):
    "Dialog listing info about the current ROM."
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("ROM Info")

        # init widgets
        self.labels = {}
        for key in ("internalname", "savedversion"):
            self.labels[key] = QLabel()

        self.patchlabels = []        
        for patchID, value in Adv3Patch.patches.items():
            self.patchlabels.append(
                (QLabel(value[0] + ":"), QLabel("<b>False<b>")))

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addWidget(QLabel("Internal name/ID:"))
        layoutMain[-1].addStretch()
        layoutMain[-1].addWidget(self.labels["internalname"])

        layoutMain.addRow()
        layoutMain[-1].addWidget(QLabel("Last saved version:"))
        layoutMain[-1].addStretch()
        layoutMain[-1].addWidget(self.labels["savedversion"])

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

        for i, patchID in enumerate(Adv3Patch.patches):
            patchflag = getattr(Adv3Attr, patchID)
            if patchflag is None:
                patchflag = "Unknown"
            self.patchlabels[i][1].setText(str(patchflag))

        super().open()

class QDialogInternalName(QDialog):
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
            QSimpleDialog(self, title="Error",
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

