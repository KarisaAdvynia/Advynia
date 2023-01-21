"""Dialogs
Various minor dialog subclasses without enough code to receive their own
module."""

# standard library imports
import os, platform
from collections.abc import Iterable

# import from other files
import AdvMetadata, AdvEditor.Number, AdvEditor.ROM
from AdvEditor import AdvWindow, Adv3Attr, Adv3Patch, Adv3Sublevel, Adv3Save
from AdvEditor.Format import pluralize
from AdvGame import GBA, SMA3
from . import PyQtImport
from .GeneralQt import *

class QDialogAbout(QDialogBase):
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

class QDialogLicenseInfo(QDialogBase):
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

class QDialogFileError(QDialogBase):
    "Generic dialog for file loading errors."
    def __init__(self, parent, filepath, text=""):
        super().__init__(parent)
        self.setWindowTitle("Error")

        labels = [QLabel("Could not load file:\n" + filepath)]
        if text:
            labels.append(QLabel(text))
            labels[-1].setWordWrap(True)

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        for label in labels:
            layoutMain.addWidget(label)
        layoutMain.addAcceptRow(self, rejectbutton=False)

        self.setFixedSize(self.sizeHint())

class QDialogLoadValidation(QDialogBase):
    "Dialog for some more specific file loading errors."
    def __init__(self, parent, *, size=None, crc32=None, savedversion=None,
                 filetypestr="hack", override=True):
        super().__init__(parent)

        if savedversion is not None:
            text = [
                "This ", filetypestr, " was created in Advynia ",
                str(savedversion), ".\nYou are using version ",
                str(AdvMetadata.version), "."
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

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(QLabel("".join(text)))

        if override:
            self.setWindowTitle("Warning")
            layoutMain.addWidget(QLabel("Try to load anyway?"))
        else:
            self.setWindowTitle("Error")

        if override:
            layoutMain.addAcceptRow(self, "Load")
        else:
            layoutMain.addAcceptRow(self, rejectbutton=False)

        self.setFixedSize(self.sizeHint())

class QDialogSaveValidation(QDialogBase):
    "Dialog for warning the user about saving over an unmodified ROM."
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Warning")

        self.checkbox = QCheckBox("Don't show this message again")

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(QLabel(
            "This ROM has not yet been modified. Are you sure?"))
        layoutMain.addWidget(self.checkbox)
        layoutMain.addAcceptRow(self, "Save")

    def accept(self):
        if self.checkbox.isChecked():
            setattr(AdvSettings, "warn_save_first", False)
        super().accept()

class QDialogPatchValidation(QDialogBase):
    "Dialog for warning the user that a patch is about to be applied."
    def __init__(self, patchkey, name, desc):
        super().__init__(AdvWindow.editor)

        self.setWindowTitle("Patch Notice")

        self.patchkey = patchkey

        # init widgets
        text = "<b>{name}</b><br>{desc}"
        label = QLabel(text.format(name=name, desc=desc))
        label.setWordWrap(True)
        self.checkbox = QCheckBox("Don't show this message again")

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(label)
        layoutMain.addWidget(QHorizLine())
        layoutMain.addWidget(self.checkbox)
        layoutMain.addAcceptRow(self, "Apply",
            labeltext="<i>Applied patches can't be reverted!</i>")

        self.setFixedSize(self.sizeHint())

    def accept(self):
        if self.checkbox.isChecked():
            setattr(AdvSettings, "warn_patch_" + self.patchkey, False)
        super().accept()

class QDialogImportPatch(QDialogBase):
    """Dialog for warning the user that one or more patches are about to be
    applied, when importing a sublevel."""
    def __init__(self, patches: Iterable[int], sublevel):
        super().__init__(AdvWindow.editor)

        self.setWindowTitle("Patch Notice")

        self.patchlist = sorted(patches)
        self.sublevel = sublevel

        # init widgets
        warninglabel = QLabel("This sublevel uses Advynia patches that are not "
            "applied to the current ROM:")
        warninglabel.setWordWrap(True)

        patchtext = []
        for patchID in self.patchlist:
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

class QDialogSMA3ImportMultiple(QDialogBase):
    """Dialog for displaying info about importing multiple files, and progress
    during importing."""
    def __init__(self, parent, text, datatosave):
        super().__init__(parent)

        self.datatosave = datatosave

        self.setWindowTitle("Import Multiple A3Ls")
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        # init widgets

        self.label = QLabel(text)
        self.label.setWordWrap(True)

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(self.label)
        layoutMain.addAcceptRow(self, "Import", addattr=True)

        layoutMain.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def accept(self):
        self.acceptbutton.setDisabled(True)
        self.rejectbutton.setDisabled(True)
        success = Adv3Save.savewrapper(
            self._importmultiple_save, *self.datatosave)
        if success:
            super().accept()
        else:
            self.acceptbutton.setEnabled(True)
            self.rejectbutton.setEnabled(True)

    def reject(self):
        """Overridden to prevent Esc from closing the dialog when importing is
        in progress."""
        if self.rejectbutton.isEnabled():
            super().reject()

    def _importmultiple_save(self,
            newsublevels, newentrances, allentrances, newmessages, newpatches):

        # apply patches, if any
        self._updateprogresstext("Applying patches...")
        Adv3Patch.applymultiplepatches(newpatches)

        # save sublevels, if any
        for sublevelID, sublevel in newsublevels.items():
            self._updateprogresstext("".join((
                "Saving sublevel ", format(sublevelID, "02X"), "...")))
            Adv3Save.savesubleveltoROM(sublevel, sublevelID)

        # update and save entrances, if any
        if allentrances:
            self._updateprogresstext("Saving level entrances...")
            Adv3Save.saveentrances(*allentrances)
        elif newentrances:
            self._updateprogresstext("Saving level entrances...")
            oldmidwaylen = (6 if (Adv3Attr.midway6byte and
                            "midway6byte" not in newpatches) else 4)
            mainentrances, midwayentrances = SMA3.importlevelentrances(
                Adv3Attr.filepath, maxmidpoints=Adv3Attr.maxmidpoints,
                midwaylen=oldmidwaylen)
            for levelID, (main, midways) in newentrances.items():
                mainentrances[levelID] = main
                midwayentrances[levelID] = midways
            Adv3Save.saveentrances(mainentrances, midwayentrances,
                                   oldmidwaylen=oldmidwaylen)

        # update and save messages, if any
        if newmessages:
            self._updateprogresstext("Saving messages...")
            messages = SMA3.importalltext(Adv3Attr.filepath)
            messages.update(newmessages)
            Adv3Save.savemessages(messages)

        return True

    def _updateprogresstext(self, text):
        self.label.setText(text)
        self.label.updateGeometry()
        QCoreApplication.processEvents()

class QDialogImportGraphics(QDialogBase):
    def __init__(self, parent, allowoverride,
                 dirwarnings, exporttypes, sizewarnings, sizeerrors, nodata):
        super().__init__(parent)

        self.setWindowTitle("Import Graphics/Tilemaps")

        # calculate text and create layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        if nodata:
            if len(exporttypes) > len(dirwarnings):
                text = "All processed files are identical to ROM data."
            else:
                text = """No importable files were found. 
Did you export graphics/tilemaps first? Exported graphics can be modified in a 
GBA tile editor."""
            label = QLabel(text)
            label.setWordWrap(True)
            layoutMain.addWidget(label)

        else:
            if dirwarnings:
                text = [pluralize(len(dirwarnings), "export folder"),
                        " could not be found:<br>",
                        "<br>".join(seq[1] for seq in dirwarnings)]
                remainingtypes = set(exporttypes).difference(
                    seq[0] for seq in dirwarnings)
                if remainingtypes:
                    text += ["<br>", remainingtypes.pop().capitalize(),
                             " can still be imported."]
                layoutMain.addWidget(QLabel("".join(text)))

            if sizeerrors:
                if layoutMain.count(): layoutMain.addWidget(QHorizLine())
                label = QLabel(
                    """<i></i>File size for uncompressed data did not match. 
Data cannot be imported since it would risk ROM data corruption.""")
                label.setWordWrap(True)
                layoutMain.addWidget(label)
                layoutMain.addLayout(_LayoutSizeGrid(sizeerrors))

            if sizewarnings:
                if layoutMain.count(): layoutMain.addWidget(QHorizLine())
                label = QLabel(
                    """<i></i>File size for compressed data did not match. 
Data can be imported, but may overflow console RAM. Importing is not 
recommended unless you know exactly what you're doing.""")
                label.setWordWrap(True)
                layoutMain.addWidget(label)
                layoutMain.addLayout(_LayoutSizeGrid(sizewarnings))

        layoutMain.addStretch()

        if allowoverride:
            layoutMain.addAcceptRow(self, accepttext="Import", rejecttext="Cancel")
        else:
            layoutMain.addAcceptRow(self, rejecttext="OK", acceptbutton=False)

class _LayoutSizeGrid(QGridLayout):
    def __init__(self, sizetable):
        super().__init__()
        self.addWidget(QLabel("File name"), 0, 0)
        self.addWidget(QLabel("File size"), 0, 1, Qt.AlignmentFlag.AlignRight)
        self.addWidget(QLabel("Expected size"), 0, 2, Qt.AlignmentFlag.AlignRight)
        row = 1
        for filename, newlen, oldlen in sizetable:
            self.addWidget(QLabel(filename), row, 0)
            self.addWidget(QLabel("0x" + format(newlen, "X")), row, 1, Qt.AlignmentFlag.AlignRight)
            self.addWidget(QLabel("0x" + format(oldlen, "X")), row, 2, Qt.AlignmentFlag.AlignRight)
            row += 1

class QDialogSelectSublevel(QDialogBase):
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
        updateset = {"Byte Text"}

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
            updatedict = Adv3Sublevel.cmpheader(SMA3.Constants.headerdefaults)
            AdvWindow.editor.setHeader(updatedict)
            updateset |= {"Header"}

        AdvWindow.statusbar.setActionText(
            "Cleared " + ", ".join(clearlist).lower() + ".")
        AdvWindow.undohistory.addaction(
            "Clear " + (clearlist[0] if len(clearlist) == 1 else "Sublevel"),
            updateset=updateset, reload=True)
        super().accept()

class QDialogSaveWarning(QDialogBase):
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
        self.labels["freespace"].setText("".join((
            AdvEditor.Number.megabytetext(freespace), "/",
            AdvEditor.Number.megabytetext(
                os.path.getsize(Adv3Attr.filepath) - 0x400000), " MiB"
            )))

        self.calcbutton.hide()
        self.labels["freespace"].show()

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
