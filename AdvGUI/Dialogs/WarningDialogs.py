# standard library imports
from collections.abc import Iterable

# import from other files
import AdvMetadata
from AdvEditor import AdvWindow, Adv3Patch
from AdvEditor.Format import pluralize
from AdvGUI.GeneralQt import *

class QDialogUnsavedWarning(QDialogBase):
    """Dialog for prompting to save unsaved changes.
    Output: 1=Save, 0=Don't Save, 2=Cancel"""
    def __init__(self, *args,
            text="Would you like to save this sublevel before closing?"):
        super().__init__(*args)

        self.setWindowTitle("Unsaved Changes")

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(QLabel(text))

        layoutMain.addRow()
        layoutMain[-1].addStretch()
        for text, func in (("Save", self.accept),
                           ("Don't Save", lambda : self.done(2)),
                           ("Cancel", self.reject)):
            button = QPushButton(text)
            if text == "OK": button.setDefault(True)
            button.clicked.connect(func)
            layoutMain[-1].addWidget(button)

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
                f"This {filetypestr} was created in Advynia {savedversion}.\n"
                f"You are using version {AdvMetadata.version}."
                ]
        elif size is not None:
            text = [
                "File did not validate as a clean SMA3 (U) ROM image.\n"
                "Expected file size: 4194304 bytes\n"
                f"Detected file size: {size} bytes"
                ]
        elif crc32 is not None:
            text = [
                "File did not validate as a clean SMA3 (U) ROM image.\n"
                "Expected CRC-32: 40A48276\n"
                f"Detected CRC-32: {crc32:08X}"
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
    def __init__(self, patches: Iterable[str], sublevel):
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
